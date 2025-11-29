# 🤖 Fake Models - A collection of fake LLM models

- **Plugin ID** : kurokobo/fake_models
- **Author** : kurokobo
- **Type** : model
- **Repository** : <https://github.com/kurokobo/dify-plugin-collection>
- **Marketplace** : <https://marketplace.dify.ai/plugins/kurokobo/fake_models>

## ✨ Overview

A collection of fake LLM models that never rely on any external service and always return dummy responses.
Models included are:

- ✅ **echo**
  - Echoes back the user's last message, with optional delay and streaming interval
- ✅ **fixed**
  - Always returns a fixed response that you configure, with optional delay and streaming interval
- ✅ **hello**
  - Returns a simple fixed response "Hello, Dify!" without any configurable parameters

These models are useful for:

- **Testing and debugging** your Dify workflows without consuming API credits
- **Simulating delays and streaming** behavior for performance testing
- **Creating demonstrations** without depending on external services
- **Reducing costs** by replacing the system model so that background (unintended) queries do not consume API credits

Intended as minimal drop-in replacements for real LLM models.

## ⚙️ Setup Instructions

After installing the plugin,

1. Go to the `Model Provider` section in `Settings` page.
2. Launch the `Setup` in the `Fake Models` card.
3. Enter any name you like for `Authorization Name` in the `API Key Authorization Configuration` modal.
4. Click `Save`.

This will make the built-in models provided by this plugin available.

**Note**: Since this plugin does not depend on any external services, this authorization setup step is actually meaningless. However, Dify cannot properly handle providers that don’t require authorization, so this step is necessary.

## 🛠️ Bundled Models

### ✅ echo

This model echoes back the user's last message.

**Parameters:**

- **delay_ms** (optional, default: 0)
  - The delay in milliseconds before responding
  - Minimum: 0

- **interval_ms** (optional, default: 0)
  - The interval in milliseconds between streaming chunks
  - Minimum: 0

- **repeat** (optional, default: 1)
  - The number of times to repeat the echoed message
  - Minimum: 1

### ✅ fixed

This model always returns a fixed response that you configure.

**Parameters:**

- **delay_ms** (optional, default: 0)
  - The delay in milliseconds before responding
  - Minimum: 0

- **interval_ms** (optional, default: 0)
  - The interval in milliseconds between streaming chunks
  - Minimum: 0

- **response** (required, default: "Hello, World!")
  - The content that the model responds with each time
  - You can set any text you want the model to return

### ✅ hello

This model returns a simple fixed response "Hello, Dify!" without any configurable parameters.
It is intended to replace the system model in order to avoid consuming real API credits when generating chat titles, for example.

**Parameters:**

None. This model has no configurable parameters and always returns "Hello, Dify!".

## Related Links

- **Icon**: [Heroicons](https://heroicons.com/)
