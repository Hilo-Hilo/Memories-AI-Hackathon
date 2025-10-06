# Batch API Reference

The Batch API allows you to process large quantities of media files asynchronously. You can submit a job with a list of URLs or local files, and the API will process them in the background and notify you when the results are ready.

## Base URL

`https://api.hume.ai/v0/batch/jobs`

## Authentication

All requests to the Batch API must include an `X-Hume-Api-Key` header with your API key.

## Endpoints

### POST /v0/batch/jobs

Starts a new inference job.

**Request Body**

| Parameter | Type | Description |
|---|---|---|
| `models` | object | (Optional) The models to run. If not specified, all models will be run. |
| `urls` | array of strings | (Optional) A list of public URLs to the media files to be processed. |
| `text` | array of strings | (Optional) A list of text strings to be processed by the language models. |
| `callback_url` | string | (Optional) A URL to which a POST request will be sent upon job completion or failure. |
| `notify` | boolean | (Optional) Whether to send an email notification upon job completion or failure. Defaults to `false`. |

**Response**

| Parameter | Type | Description |
|---|---|---|
| `job_id` | string | The unique identifier for the started job. |

### GET /v0/batch/jobs

Lists all jobs.

**Query Parameters**

| Parameter | Type | Description |
|---|---|---|
| `limit` | integer | (Optional) The maximum number of jobs to return. Defaults to 50. |
| `status` | array of enums | (Optional) Filter jobs by status. Possible values are `QUEUED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`. |

**Response**

A list of job objects.

### GET /v0/batch/jobs/:id

Retrieves the details of a specific job.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | The unique identifier for the job. |

**Response**

A job object with detailed information about the job, including its status, request parameters, and timestamps.

### GET /v0/batch/jobs/:id/predictions

Retrieves the predictions for a completed job.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | The unique identifier for the job. |

**Response**

A JSON object containing the predictions for each file in the job.

### GET /v0/batch/jobs/:id/artifacts

Retrieves the artifacts for a completed job, such as saved faces.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | The unique identifier for the job. |

**Response**

A zip file containing the job artifacts.

