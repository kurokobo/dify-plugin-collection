# 🎁 Dify Plugin Collection

A repository of various plugins for Dify, developed by [@kurokobo](https://github.com/kurokobo). All plugins in this repository are available on the [Dify Marketplace](https://marketplace.dify.ai/).

## 📦 Tool Plugins

<!-- ls: tools -->
- [📁 File Tools v0.0.1 (tools/file_tools)](/tools/file_tools)
  - A collection of various tools for handling file object.
- [📁 Knowledge Toolbox v0.0.2 (tools/knowledge_toolbox)](/tools/knowledge_toolbox)
  - Small tools for working with Dify Knowledge API.
<!-- /ls: tools -->

## 🚀 Release Process

By creating a new release with a tag in the format `<plugin_type>/<plugin_name>/<version>`, the following actions will be triggered:

1. Validate the tag to ensure the plugin type, name, and version are matched with the existing plugin directory structure and its manifest.
2. Package the specified plugin into a `difypkg` file.
3. Clone the forked official `dify-plugins` repository and add the packaged plugin file to the desired directory.
4. Commit and push the changes to the forked repository.

Then manually create a pull request to the official `dify-plugins` repository.

Refer to [the exising releases](https://github.com/kurokobo/dify-plugin-collection/releases), [the workflow](/.github/workflows/plugin-publish.yml), and [its logs](https://github.com/kurokobo/dify-plugin-collection/actions) to see the release process in action.
