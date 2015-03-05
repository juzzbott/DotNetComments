import sublime, sublime_plugin, re

CODE_SECTION_PROP = 1
CODE_SECTION_CLASS = 2
CODE_SECTION_METHOD = 4
CODE_SECTION_METHOD_WITH_RETURN = 8
CODE_SECTION_CONSTRUCOR = 16

MAX_LINE_SEARCH = 15

class XmlComments(sublime_plugin.EventListener):
	def on_modified(self, view):

		# Get the file type. If we are not a .cs file, then just exit
		syntax_type = view.settings().get('syntax')
		if not re.match('.*C#.tmLanguage', syntax_type):
			return

		# Iterate through the regions in the view selection.
		region = view.sel()[0]

		# Ensure the region is empty (no selection)
		if region.empty():

			# Get the line and the contents of the line
			line = view.line(region)
			line_contents = view.substr(line).strip();

			if line_contents == '' or line_contents[0] is not '/':
				return

			# Ensure we have a comment before proceeding
			if line_contents == '///':

				# get the next line contents
				next_line_contents = get_next_line_contents(view, -1)

				# to prevent recusive comment display, ensure we are not in the middle of a comment block
				if next_line_contents[0].strip() == '/// </summary>':
					return

				# Get the code section type based on the next line of code.
				code_section_type = get_code_section_type(next_line_contents[0], -1, view, 0)
				
				# Get the comment block based on the code section type and add to the buffer.
				comment_block = get_comment_text(code_section_type, view);
				view.run_command('xml_summary_comment', {"args":{'comment_block': comment_block}})


class XmlSummaryCommentCommand(sublime_plugin.TextCommand):
	def run(self, edit, args):

		# Add the comment block to the page
		pos = self.view.sel()[0].begin()
		self.view.insert(edit, pos, args["comment_block"][0])

		# Get the point to place the cursor at
		pt = self.view.text_point(args["comment_block"][1], args["comment_block"][2])

		# Set the cursor on the buffer 
		self.view.sel().clear()
		self.view.sel().add(sublime.Region(pt))

		# show the cursor
		self.view.show(pt)


def get_next_line_contents(view, line):

	# get current line number
	region = view.sel()[0]
	rowcol = view.rowcol(region.begin())

	next_line = line

	if next_line == -1:
		next_line = rowcol[0]

	next_line = next_line + 1

	# get next line's starting point
	next_row_starting = view.text_point(next_line, 0)

	# get the whole next line
	next_row_region = view.line(next_row_starting)
	next_line_contents = view.substr(next_row_region)

	return (next_line_contents, next_line)


def get_comment_text(code_section_type, view):

	# get the settings for the tab size and use tabs
	settings = view.settings()
	tab_size = int(settings.get('tab_size', 8))
	use_spaces = settings.get('translate_tabs_to_spaces')

	# get the column value so we can build the indent size
	rowcol = view.rowcol(view.sel()[0].begin())
	column = rowcol[1]
	indent = ''

	# subtract 3 to get the right column value (start of line)
	column = column - 3

	for i in range(column):
		indent = indent + (' ' if use_spaces else '\t')

	# get the positions to set the cursor to when the comment is added to the page
	cursor_line = rowcol[0] + 1
	cursor_column = column + 4

	if code_section_type == CODE_SECTION_CLASS:
		return (' <summary>\n' + indent + '/// \n' + indent + '/// </summary>', cursor_line, cursor_column)
	elif code_section_type == CODE_SECTION_CONSTRUCOR:
		return (' <summary>\n' + indent + '/// \n' + indent + '/// </summary>', cursor_line, cursor_column)
	elif code_section_type == CODE_SECTION_METHOD_WITH_RETURN:
		return (' <summary>\n' + indent + '/// \n' + indent + '/// </summary>\n' + indent + '/// <returns></returns>', cursor_line, cursor_column)
	else:
		return (' <summary>\n' + indent + '/// \n' + indent + '/// </summary>', cursor_line, cursor_column)


def get_code_section_type(line_contents, line, view, recurse_level):

	# if it's an empty line, get the next line
	if (line_contents.strip() == '') or (line_contents.strip()[0] == '['):
		# Have our recurse text only go down the MAX_LINE_SEARCH to prevent excessive recursion
		if recurse_level <= MAX_LINE_SEARCH:
			recurse_level += 1
			next_line_contents = get_next_line_contents(view, line)
			return get_code_section_type(next_line_contents[0], (next_line_contents[1] + 1), view, recurse_level)

	# Check for a property or field type
	if re.match('^\s+(([a-z][a-zA-Z0-9_]*\s+)+([a-zA-Z_][a-zA-Z0-9_]+))\s*;?[^(]*$', line_contents):
		return CODE_SECTION_PROP
	# Check for a class type
	elif re.match('^\s+(([a-z][a-zA-Z0-9_]*\s+)+class\s+([a-zA-Z_][a-zA-Z0-9_]+))\s*\(?.*$', line_contents):
		return CODE_SECTION_CLASS
	# Check for a void method
	elif re.match('^\s+(([a-z][a-zA-Z0-9_]*\s+)+void\s+([a-zA-Z_][a-zA-Z0-9_]+))\s*\(.*$', line_contents):
		return CODE_SECTION_METHOD
	# Check for a class constructor
	elif re.match('^\s+(((public)\s+|(private)\s+|(internal)\s+|(protected)\s+)*([a-zA-Z_][a-zA-Z0-9_]+))\s*\(.*$', line_contents):
		return CODE_SECTION_CONSTRUCOR
	# Check for the method that returns a value
	elif re.match('^\s+(([a-z][a-zA-Z0-9_]*\s+)+([a-zA-Z_][a-zA-Z0-9_]+))\s*\(.*$', line_contents):
		return CODE_SECTION_METHOD_WITH_RETURN
	# Default to a propety 
	else:
		return CODE_SECTION_PROP