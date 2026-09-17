# Privacy Policy

This plugin uses a configured OpenAI or Azure OpenAI service to rank search documents. Protecting user privacy is our top priority.

## Types of Data Collected

This plugin handles only the following data:

- Search queries and candidate document text provided by Dify
- A SHA-256 hash of the Dify user identifier when one is provided
- Provider credentials and configuration, including the API key, endpoint, and model or deployment name
- Ranking responses returned by the configured service

No other information, such as a user's name or email address, is collected by the plugin.

## How We Use Your Data

The plugin uses this data exclusively for the following purposes:

- To ask the configured model to rank candidate documents against a search query
- To authenticate requests to the selected service
- To send a pseudonymous safety identifier when Dify supplies a user identifier

Your data is not used by the plugin for training, profiling, or marketing.

## Data Sharing and Disclosure

Queries, candidate document text, the pseudonymous safety identifier, and credentials are transmitted only to the OpenAI or Azure OpenAI endpoint selected by the user. The plugin does not share data with any other third party.

## Use of Third-party Services

This plugin relies on one of the following external services:

- **OpenAI**: Requests are processed by the OpenAI API. Refer to [OpenAI's privacy policy](https://openai.com/privacy/) and [API data usage policies](https://platform.openai.com/docs/guides/your-data).
- **Azure OpenAI**: Requests are processed by Microsoft Azure. Refer to [Microsoft's privacy statement](https://privacy.microsoft.com/) and [Azure OpenAI data privacy documentation](https://learn.microsoft.com/azure/ai-foundry/responsible-ai/openai/data-privacy).

The plugin requests that the Responses API does not store responses by setting `store` to `false`. Data handling and retention by the selected service remain governed by that service's configuration and terms.

## Data Retention and Management

This plugin does not request storage permissions and does not independently persist queries, documents, credentials, user identifiers, or model responses. Data managed by Dify or the configured external service is outside the plugin's storage control.

## Your Rights

You may remove the model configuration or uninstall this plugin at any time.

## Policy Updates

This policy may be updated from time to time due to feature additions or legal requirements. Please refer to the latest policy in the repository for updates.

## Contact Us

If you have any questions regarding privacy, please contact us at:

- [Open an issue on GitHub](https://github.com/kurokobo/dify-plugin-collection/issues)
- [@kurokobo on GitHub](https://github.com/kurokobo)
