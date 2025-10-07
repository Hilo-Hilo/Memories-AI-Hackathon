# Limits and Quotas

The Hume Expression Measurement API has certain limits and quotas to ensure fair usage and system stability. Understanding these limits is important for planning your integration.

## Rate Limits

The API implements rate limiting to prevent abuse and ensure service availability for all users. When you exceed the rate limit, you will receive a 429 (Too Many Requests) response.

The SDKs automatically handle rate limit errors by implementing exponential backoff and retry logic. However, you should design your application to avoid hitting rate limits in the first place by spacing out requests appropriately.

## File Size Limits

There are practical limits on the size of files that can be processed through the API. Very large files may take significant time to process and could time out.

For batch processing, consider splitting very large media files into smaller segments. This not only helps with processing time but also makes it easier to handle errors and retry failed segments.

## Concurrent Requests

The number of concurrent requests you can make may be limited based on your account tier. If you need higher concurrency limits for your application, contact the Hume AI team to discuss enterprise options.

## Job Retention

Completed jobs and their results are retained for a limited time before being automatically deleted. Make sure to retrieve and store any results you need before they expire.

The exact retention period may vary, so consult the official documentation or contact support for current policies.

## Archive Processing

When submitting archives (zip, tar.gz, etc.) for batch processing, there are limits on the number of files within an archive and the total size of the archive.

For very large collections of files, consider splitting them into multiple archives and submitting separate jobs. This also provides better parallelization and faster overall processing.

## URL Limits

When submitting URLs for batch processing, there is a recommended limit of 100 URLs per request. For larger batches, package the files into archives rather than submitting individual URLs.

## Enterprise Options

If the standard limits do not meet your needs, enterprise plans are available with higher quotas and custom configurations. Enterprise customers can also receive volume discounts on API usage.

Contact the Hume AI sales team to discuss enterprise options and custom pricing.
