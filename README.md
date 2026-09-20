# Scout Connector

> Built with [Oya AI](https://getoya.ai)

## About

You are Scout — an AI recruiting assistant, and you say so plainly. You are not pretending to be a person, and you never apologise for being an agent; being one is the whole point of the demo.
You are quick, concrete and a little dry. You write the way a good recruiter texts: short lines, one thought at a time, no preamble, no corporate throat-clearing.
You are talking to someone who just looked at sendscout.ai and left. They are curious, not committed. You earn the next message, every message.
You would rather show than tell. When someone names a role, you start working it immediately — intake questions, a real outreach draft, a real interview link — instead of explaining your features.
You never oversell, never use hype words, and never claim a capability or a customer you cannot point to in the knowledge base.
You treat the Scout Connector LinkedIn account as the scarce asset it is: it is a brand-new account with no history, and every restriction warning matters more than any single send.

## Configuration

- **Mode:** skills
- **Agent ID:** `b841433a-0b2f-45b1-adfa-34f4808bbb85`
- **Model:** `gemini/gemini-3.5-flash`

## Usage

Every deployed agent exposes an **OpenAI-compatible API endpoint**. Use any SDK or HTTP client that supports the OpenAI chat completions format.

### Authentication

Pass your API key via either header:
- `Authorization: Bearer a2a_your_key_here`
- `X-API-Key: a2a_your_key_here`

Create API keys at [https://getoya.ai/api-keys](https://getoya.ai/api-keys).

### Endpoint

```
https://getoya.ai/api/v1/chat/completions
```

### cURL

```bash
curl -X POST https://getoya.ai/api/v1/chat/completions \
  -H "Authorization: Bearer a2a_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini/gemini-3.5-flash","messages":[{"role":"user","content":"Hello"}]}'

# Continue a conversation using thread_id from the first response:
curl -X POST https://getoya.ai/api/v1/chat/completions \
  -H "Authorization: Bearer a2a_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini/gemini-3.5-flash","messages":[{"role":"user","content":"Follow up"}],"thread_id":"THREAD_ID"}'
```

### Python

```python
from openai import OpenAI

client = OpenAI(
    api_key="a2a_your_key_here",
    base_url="https://getoya.ai/api/v1",
)

# First message — starts a new thread
response = client.chat.completions.create(
    model="gemini/gemini-3.5-flash",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)

# Continue the conversation using thread_id
thread_id = response.thread_id
response = client.chat.completions.create(
    model="gemini/gemini-3.5-flash",
    messages=[{"role": "user", "content": "Follow up question"}],
    extra_body={"thread_id": thread_id},
)
print(response.choices[0].message.content)
```

### TypeScript

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "a2a_your_key_here",
  baseURL: "https://getoya.ai/api/v1",
});

// First message — starts a new thread
const response = await client.chat.completions.create({
  model: "gemini/gemini-3.5-flash",
  messages: [{ role: "user", content: "Hello" }],
});
console.log(response.choices[0].message.content);

// Continue the conversation using thread_id
const threadId = (response as any).thread_id;
const followUp = await client.chat.completions.create({
  model: "gemini/gemini-3.5-flash",
  messages: [{ role: "user", content: "Follow up question" }],
  // @ts-ignore — custom field
  thread_id: threadId,
});
console.log(followUp.choices[0].message.content);
```

### Swift

```swift
// Package.swift:
// .package(url: "https://github.com/MacPaw/OpenAI.git", from: "0.4.0")
import Foundation
import OpenAI

@main
struct Main {
    static func main() async throws {
        let config = OpenAI.Configuration(
            token: "a2a_your_key_here",
            host: "getoya.ai",
            scheme: "https"
        )
        let client = OpenAI(configuration: config)

        let query = ChatQuery(
            messages: [.user(.init(content: .string("Hello")))],
            model: "gemini/gemini-3.5-flash"
        )
        let result = try await withCheckedThrowingContinuation { continuation in
            _ = client.chats(query: query) { continuation.resume(with: $0) }
        }
        print(result.choices.first?.message.content ?? "")
    }
}
```

### Kotlin

```kotlin
// build.gradle.kts dependencies:
// implementation("com.aallam.openai:openai-client:4.0.1")
// implementation("io.ktor:ktor-client-cio:3.0.0")
import com.aallam.openai.api.chat.ChatCompletionRequest
import com.aallam.openai.api.chat.ChatMessage
import com.aallam.openai.api.chat.ChatRole
import com.aallam.openai.api.model.ModelId
import com.aallam.openai.client.OpenAI
import com.aallam.openai.client.OpenAIHost
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    val openai = OpenAI(
        token = "a2a_your_key_here",
        host = OpenAIHost(baseUrl = "https://getoya.ai/api/v1/")
    )
    val completion = openai.chatCompletion(
        ChatCompletionRequest(
            model = ModelId("gemini/gemini-3.5-flash"),
            messages = listOf(ChatMessage(role = ChatRole.User, content = "Hello"))
        )
    )
    println(completion.choices.first().message.messageContent)
}
```

### Streaming

```python
stream = client.chat.completions.create(
    model="gemini/gemini-3.5-flash",
    messages=[{"role": "user", "content": "Tell me about AI agents"}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
```

### Embeddable Widget

```html
<!-- Oya Chat Widget -->
<script
  src="https://getoya.ai/widget.js"
  data-agent-id="b841433a-0b2f-45b1-adfa-34f4808bbb85"
  data-api-key="a2a_your_key_here"
  data-title="Scout Connector"
></script>
```

### Supported Models

- `gemini/gemini-2.0-flash`
- `gemini/gemini-2.5-flash`
- `gemini/gemini-2.5-pro`
- `gemini/gemini-3.5-flash`
- `gemini/gemini-3.1-pro-preview`
- `anthropic/claude-sonnet-4-6`
- `anthropic/claude-haiku-4-5-20251001`

---

*Managed by [Oya AI](https://getoya.ai). Do not edit manually — changes are overwritten on each sync.*