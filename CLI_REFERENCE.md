# Syntra CLI Connection Guide

## Quick Setup

### 1. Get Your API Key

1. Go to: `https://syntra.goalixa.com/admin`
2. Navigate to **Users** → Select your user
3. Go to **API Keys** tab
4. Click **Create API Key**
5. Copy the key (it's only shown once!)

### 2. Configure CLI

```bash
# Option A: Using Syntra CLI
syntra configure --api-key sk_abc123... --api-endpoint https://api.goalixa.com

# Option B: Using environment variable
export SYNTRA_API_KEY="sk_abc123..."
export SYNTRA_API_ENDPOINT="https://api.goalixa.com"

# Option C: Using config file
echo "export SYNTRA_API_KEY=sk_abc123..." >> ~/.bashrc
echo "export SYNTRA_API_ENDPOINT=https://api.goalixa.com" >> ~/.bashrc
source ~/.bashrc
```

## API Usage Examples

### cURL

```bash
# Set your API key
export SYNTRA_API_KEY="sk_abc123..."

# Check rate limits
curl https://api.goalixa.com/api/rate-limit \
  -H "X-API-Key: $SYNTRA_API_KEY"

# Make a request
curl -X POST https://api.goalixa.com/api/ask \
  -H "X-API-Key: $SYNTRA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "List all pods with issues",
    "namespace": "production"
  }'
```

### Python

```python
import os
import requests

API_KEY = os.environ.get("SYNTRA_API_KEY")
API_ENDPOINT = "https://api.goalixa.com"

def ask_syntra(prompt, namespace="default"):
    """Ask Syntra AI for help with DevOps tasks."""
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt,
        "namespace": namespace
    }

    response = requests.post(
        f"{API_ENDPOINT}/api/ask",
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()
    return response.json()

# Usage
result = ask_syntra("Check pod status in production", "production")
print(result["response"])
```

### Node.js

```javascript
const https = require('https');

const API_KEY = process.env.SYNTRA_API_KEY;
const API_ENDPOINT = 'https://api.goalixa.com';

async function askSyntra(prompt, namespace = 'default') {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({ prompt, namespace });

    const options = {
      hostname: 'api.goalixa.com',
      path: '/api/ask',
      method: 'POST',
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json',
        'Content-Length': data.length
      }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => resolve(JSON.parse(body)));
    });

    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// Usage
askSyntra('Check pod status', 'production')
  .then(result => console.log(result.response))
  .catch(console.error);
```

### Go

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "os"
)

const APIEndpoint = "https://api.goalixa.com"

type SyntraRequest struct {
    Prompt    string `json:"prompt"`
    Namespace string `json:"namespace"`
}

type SyntraResponse struct {
    Response  string `json:"response"`
    AgentUsed string `json:"agent_used"`
}

func AskSyntra(prompt, namespace string) (*SyntraResponse, error) {
    apiKey := os.Getenv("SYNTRA_API_KEY")

    reqBody := SyntraRequest{
        Prompt:    prompt,
        Namespace: namespace,
    }

    jsonData, _ := json.Marshal(reqBody)

    req, _ := http.NewRequest("POST", APIEndpoint+"/api/ask", bytes.NewReader(jsonData))
    req.Header.Set("X-API-Key", apiKey)
    req.Header.Set("Content-Type", "application/json")

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    body, _ := io.ReadAll(resp.Body)

    var result SyntraResponse
    json.Unmarshal(body, &result)

    return &result, nil
}

func main() {
    result, err := AskSyntra("Check pod status", "production")
    if err != nil {
        fmt.Println("Error:", err)
        return
    }

    fmt.Println(result.Response)
}
```

### Rust

```rust
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::env;

const API_ENDPOINT: &str = "https://api.goalixa.com";

#[derive(Serialize)]
struct SyntraRequest {
    prompt: String,
    namespace: String,
}

#[derive(Deserialize)]
struct SyntraResponse {
    response: String,
    agent_used: String,
}

async fn ask_syntra(prompt: &str, namespace: &str) -> Result<SyntraResponse, Box<dyn std::error::Error>> {
    let client = Client::new();
    let api_key = env::var("SYNTRA_API_KEY")?;

    let req_body = SyntraRequest {
        prompt: prompt.to_string(),
        namespace: namespace.to_string(),
    };

    let response = client
        .post(format!("{}/api/ask", API_ENDPOINT))
        .header("X-API-Key", api_key)
        .json(&req_body)
        .send()
        .await?;

    let result: SyntraResponse = response.json().await?;
    Ok(result)
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let result = ask_syntra("Check pod status", "production").await?;
    println!("{}", result.response);
    Ok(())
}
```

## Rate Limiting

| Limit | Value |
|-------|-------|
| Requests per minute | 60 |
| Requests per hour | 1000 |
| Burst | 20 requests |

Check your current status:
```bash
curl https://api.goalixa.com/api/rate-limit \
  -H "X-API-Key: $SYNTRA_API_KEY" | jq
```

## Error Handling

### 401 Unauthorized
```json
{
  "detail": "Invalid API key"
}
```
**Solution**: Check your API key is correct and active.

### 403 Forbidden
```json
{
  "detail": "User account is suspended"
}
```
**Solution**: Contact admin to activate your account.

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded: max 60 requests per minute",
  "Retry-After": "60"
}
```
**Solution**: Wait before making more requests.

## Best Practices

1. **Store API Keys Securely**
   - Never hardcode API keys in source code
   - Use environment variables or secret managers
   - Rotate keys regularly

2. **Handle Rate Limits**
   - Implement exponential backoff
   - Check rate limit status before requests
   - Cache responses when appropriate

3. **Error Handling**
   - Always handle 429 responses with Retry-After
   - Log errors for debugging
   - Implement retry logic for transient failures

4. **Security**
   - Use HTTPS only
   - Never expose API keys in logs
   - Validate API responses

## Testing Your Connection

```bash
# Test script
#!/bin/bash

API_KEY="${SYNTRA_API_KEY}"
API_ENDPOINT="https://api.goalixa.com"

echo "Testing Syntra API connection..."

# Test 1: Health check (no auth)
echo "1. Health check..."
curl -s https://api.goalixa.com/api/health | jq

# Test 2: Rate limit check
echo "2. Rate limit status..."
curl -s "$API_ENDPOINT/api/rate-limit" \
  -H "X-API-Key: $API_KEY" | jq

# Test 3: Make a request
echo "3. Making test request..."
curl -s -X POST "$API_ENDPOINT/api/ask" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Say hello"}' | jq

echo "Done!"
```

## Support

- **Documentation**: https://syntra.goalixa.com/docs
- **Admin Panel**: https://syntra.goalixa.com/admin
- **API Docs**: https://api.goalixa.com/docs
- **Issues**: https://github.com/goalixa/syntra/issues
