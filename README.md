## DotNetComments
DotNetComments is a plugin for Sublime Text 3 that replicates the commenting functionality of Visual Studio. 

To use the plugin, type '///' and the plugin with automatically determine the type of comment block to generate based on the next line of code. The plugin will ignore [Attributes] so that is able to correctly determine the comment type.

Once the comment block has been generated, the cursor is automatically shifted to the entry section for the `<summary>` so that typing is unimpeeded.

### Supported comment types
The plugin can support the following comment types:
* Properties and fields
* Classes, interfaces and enumerations
* Contstructors
* Methods (both with and without return values)
* Generic TypeParam methods (<T>)

### Examples
Property comment block:
```c#
/// <summary>
/// 
/// </summary>
private int _someValue { get; set; }
```

Generic method with return value:
```c#
/// <summary>
/// 
/// </summary>
/// <typeparam name="T"></typeparam>
/// <param name="objectId"></param>
/// <param name="count"></param>
/// <returns></returns>
public static T GetObject<T>(string objectId, int count)
{
}
```

### Supported versions
So far, this has only been tested on Sublime Text 3, as it's designed to work along side plugins like OmniSharp. When I get a chance, I'll test this on Sublime Text 2.
