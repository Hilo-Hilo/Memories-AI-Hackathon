# Image Input and Token Calculation

## Image Input Requirements

### File Format Requirements
- **Supported Formats:** PNG (.png), JPEG (.jpeg, .jpg), WEBP (.webp), Non-animated GIF (.gif)
- **Size Limits:** 
  - Up to 20MB per image
  - Up to 500 individual images per request
  - Up to 50 MB image bytes per request
- **Resolution:**
  - Low-resolution: 512px x 512px
  - High-resolution: 768px (short side) x 2000px (long side)
- **Content Requirements:**
  - No watermarks or logos
  - No NSFW content
  - Clear enough for human understanding

### Image Detail Levels
- **`low`**: 85 tokens, 512px x 512px processing
- **`high`**: Full resolution processing with detailed crops
- **`auto`**: Model decides automatically (default)

## Token Calculation by Model

### GPT-4.1 Series Token Calculation
**Base Calculation:**
- Calculate number of 32px x 32px patches needed to cover image
- If patches exceed 1536, scale image down to fit within 1536 patches
- Token cost = number of patches (capped at 1536 tokens)

**Model-Specific Multipliers:**
- **gpt-4.1-mini:** Image tokens × 1.62 = total tokens
- **gpt-4.1-nano:** Image tokens × 2.46 = total tokens
- Tokens billed at normal text token rates

**Examples:**
- 1024 x 1024 image = 1024 tokens
  - (1024 + 32 - 1) // 32 = 32 patches per side
  - 32 × 32 = 1024 tokens
- 1800 x 2400 image = 1452 tokens (after scaling)

### GPT-4o and o-series Token Calculation
**Low Detail (`"detail": "low"`):**
- Fixed cost: 85 tokens (regardless of size)

**High Detail (`"detail": "high"`):**
1. Scale to fit in 2048px x 2048px square (maintain aspect ratio)
2. Scale so shortest side is 768px
3. Count 512px squares (each costs 170 tokens)
4. Add 85 base tokens

**Examples:**
- 1024 x 1024 (high detail) = 765 tokens
  - Scale to 768 x 768
  - 4 tiles × 170 + 85 = 765 tokens
- 2048 x 4096 (high detail) = 1105 tokens
  - Scale to 768 x 1536
  - 6 tiles × 170 + 85 = 1105 tokens

## API Request Syntax

### Basic Image Input (JavaScript)
```javascript
import OpenAI from "openai";

const openai = new OpenAI();

const response = await openai.responses.create({
  model: "gpt-4.1-mini",
  input: [
    {
      role: "user",
      content: [
        { type: "input_text", text: "What's in this image?" },
        {
          type: "input_image",
          image_url: "https://example.com/image.jpg",
          detail: "high" // or "low" or "auto"
        }
      ]
    }
  ]
});

console.log(response.output_text);
```

### Multiple Image Inputs
```javascript
const response = await openai.responses.create({
  model: "gpt-4.1-mini",
  input: [
    {
      role: "user",
      content: [
        { type: "input_text", text: "What are in these images?" },
        { type: "input_image", image_url: "https://example.com/image1.jpg" },
        { type: "input_image", image_url: "https://example.com/image2.jpg" }
      ]
    }
  ]
});
```

### Image Input Methods
1. **URL:** Provide fully qualified URL to image file
2. **Base64:** Provide Base64-encoded data URL

