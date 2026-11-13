# Agent guidance

Keep this plugin aligned with the supported Groundworkers plugin contract. Check the Groundworkers version range in `pyproject.toml` before relying on a host API. Do not edit Groundworkers from this repository; make a separate host change when one is required.

## If you add query embeddings or vector search

- Keep MCP tools that encode queries asynchronous. Use `await model_backend.async_embed_texts([text], role=EmbeddingRole.QUERY)`, then pass the vector to the synchronous reader lookup. Do not call synchronous embedding APIs from the MCP event loop, or work around that with `asyncio.run` or a worker thread.
- Resolve embedding model records from the relevant vector-store registry. Use the registered record's model, provider, metric, dimensions, and index configuration. Before live encoding, confirm the backend matches the registered model and provider. If the live model is not registered, raise `NOT_FOUND`; never fall back to another registered model. Stored-vector queries against the host store must use a vector from that same registered model and provider.
- Open and close **plugin-owned** DuckDB stores per operation. Never close what `context.embedding_backend_factory()` returns: it is the host's shared reader, and the host owns its lifecycle. Make sure setup commands can open a writer after readiness or a query has run.
- Report backend and store failures with public `GroundworkersError` codes. Use `embedding_store_error` to map store failures. Reserve empty-result responses for valid queries that found no match.
- Keep embedding tests isolated from user data. Exercise registered tools on a running event loop with an async-only fake backend whose synchronous method raises; cover missing and incompatible model records; and verify a writer can acquire an isolated DuckDB file after a query. Gate real-backend integration tests behind an explicit opt-in config.

When Groundworkers documentation and implementation differ, follow the documented contract for the supported version and report the discrepancy. Do not copy private host helpers into the plugin as a substitute for a supported API.
