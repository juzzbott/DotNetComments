import sublime, sublime_plugin, re

CODE_SECTION_PROP = 1
CODE_SECTION_CLASS = 2
CODE_SECTION_METHOD = 4
CODE_SECTION_METHOD_WITH_RETURN = 8
CODE_SECTION_CONSTRUCTOR = 16

MAX_LINE_SEARCH = 15

class DotNetComments(sublime_plugin.EventListener):
	def on_modified(self, view):

		# Get the file type. If we are not a .cs file, then just exit
		if not view.match_selector(0, "source.cs"):	
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
				add_comments_to_file(view)


class DotNetSummaryCommentCommand(sublime_plugin.TextCommand):
	def run(self, edit, comment_block):

		# Add the comment block to the page
		pos = self.view.sel()[0].begin()
		self.view.insert(edit, pos, comment_block[0])

		# Get the point to place the cursor at
		pt = self.view.text_point(comment_block[1], comment_block[2])

		# Set the cursor on the buffer 
		self.view.sel().clear()
		self.view.sel().add(sublime.Region(pt))

		# show the cursor
		self.view.show(pt)


def add_comments_to_file(view):	

	# get the next line contents
	next_line_contents = get_next_line_contents(view, -1)

	# to prevent recusive comment display, ensure we are not in the middle of a comment block
	if next_line_contents[0].strip()[:3] == '///':
		return

	# Get the code section type based on the next line of code.
	code_section_type = get_code_section_type(next_line_contents[0], -1, view, 0)

	# Get the comment block based on the code section type and add to the buffer.
	comment_block = get_comment_text(code_section_type, next_line_contents[0], view);
	view.run_command('dot_net_summary_comment', {'comment_block': comment_block})


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


def get_comment_text(code_section_type, line_contents, view):

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

	# define the parameter comment block
	parameter_comment_block = ''

	# Get the new line chars based on the settings/system
	nl_char = get_new_line_chars(view)

	# If it's a method or a constructor, then we should also look for the parameters to add to the comment block as well
	if code_section_type == CODE_SECTION_CONSTRUCTOR or code_section_type == CODE_SECTION_METHOD or code_section_type == CODE_SECTION_METHOD_WITH_RETURN:
		raw_parameters = get_parameters_for_method(view, view.sel()[0])
		parameter_comment_block = build_parameter_comments(raw_parameters, indent, nl_char)
		if parameter_comment_block is None:
			parameter_comment_block = ""

	if code_section_type == CODE_SECTION_CLASS:
		return (' <summary>' + nl_char + indent + '/// ' + nl_char + indent + '/// </summary>', cursor_line, cursor_column)
	elif code_section_type == CODE_SECTION_CONSTRUCTOR or code_section_type == CODE_SECTION_METHOD:
		return (' <summary>' + nl_char + indent + '/// ' + nl_char + indent + '/// </summary>' + parameter_comment_block, cursor_line, cursor_column)
	elif code_section_type == CODE_SECTION_METHOD_WITH_RETURN:
		type_param_block = ''

		# If there is a type parameter (ie <T>) add the type parameter
		match = re.search('^\s*[<>\w\s]*\s+([a-zA-Z_][\w]+)(?:<([A-Za-z]*)>)\s*\(.*$', line_contents)	
		if match is not None:
			type_param_block = nl_char + indent + '/// <typeparam name="' + match.group(2) + '"></typeparam>'

		return (' <summary>' + nl_char + indent + '/// ' + nl_char + indent + '/// </summary>' + type_param_block + parameter_comment_block +  + nl_char + indent + '/// <returns></returns>', cursor_line, cursor_column)
	else:
		return (' <summary>' + nl_char + indent + '/// ' + nl_char + indent + '/// </summary>', cursor_line, cursor_column)


def get_code_section_type(line_contents, line, view, recurse_level):

	# if it's an empty line, get the next line
	if (line_contents.strip() == '') or (line_contents.strip()[0] == '['):
		# Have our recurse text only go down the MAX_LINE_SEARCH to prevent excessive recursion
		if recurse_level <= MAX_LINE_SEARCH:
			recurse_level += 1
			next_line_contents = get_next_line_contents(view, line)
			return get_code_section_type(next_line_contents[0], (next_line_contents[1] + 1), view, recurse_level)
		else:
			# default to property if recusion limit reached
			return CODE_SECTION_PROP

	# Check for a class type
	if re.match('^\s*(?:[a-z][\w]*\s+)+(?:class|interface|enum)\s+([a-zA-Z_][\w]+)\s*\{?.*$', line_contents):
		return CODE_SECTION_CLASS
	# Check for a void method
	elif re.match('^\s*(?:[a-z][\w]*\s+)+void\s+([a-zA-Z_][\w]+)\s*\(.*$', line_contents):
		return CODE_SECTION_METHOD
	# Check for a class constructor
	elif re.match('^\s*(?:public\s+|private\s+|internal\s+|protected\s+)+([a-zA-Z_][\w]+)\s*\(.*$', line_contents):
		return CODE_SECTION_CONSTRUCTOR
	# Check for the method that returns a value
	elif re.match('^\s*[<>\w\s]*\s+([a-zA-Z_][\w]+)<?[A-Za-z]*>?\s*\(.*$', line_contents):
		return CODE_SECTION_METHOD_WITH_RETURN
	# Default to a propety 
	else:
		return CODE_SECTION_PROP


def build_parameter_comments(raw_parameters, indent, nl_char):

	# replace all commas within quotes with nothing, so that we can just split by comma
	raw_parameters = re.sub('([()])|("[^"]*")', '', raw_parameters)

	# Split by comma to get each parameter
	split_parameters = re.split(',', raw_parameters)

	comment_parameters_block = ''

	for raw_parameter in split_parameters:
		match = re.search('^\s*.*\s+(\w+)\s*.*$', raw_parameter.strip())

		# If there is a match, then add to the comment block
		if match is not None:
			comment_parameters_block += nl_char + indent + '/// <param name="' + match.group(1) + '"></param>'

	return comment_parameters_block


def get_parameters_for_method(view, region):

	# Get the region that encloses the regex to get all parameters between the ()
	parameters_region = view.find('\(.*\)', region.begin())
	parameters_text = view.substr(parameters_region)

	if parameters_text is None:
		parameters_text = ''

	return parameters_text


def get_new_line_chars(view):

	# Get the setting object from the view
	settings = view.settings()

	# Get the default line ending
	default_line_ending = settings.get('default_line_ending', 'system')

	# Set the default line ending char to be linux/mac
	newline_char = '\n'

	# If settings are set to windows, or we are on a windows system, then change to CRLF
	if default_line_ending == 'windows':
		newline_char = '\r\n'
	elif default_line_ending == 'system':
		if sublime.platform() == 'windows':
			newline_char = '\r\n'

	return newline_char