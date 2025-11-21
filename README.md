# WeavETL
**What if you could query any data source like a SQL database?**

**weavETL** is a thin, declarative layer that turns diverse sources—APIs, SaaS apps, files, services—into queryable, trustworthy “datasets” without building bespoke pipelines first.

- **One idea:** separate _what the data is_ from _how to get it_ and _what you want to do with it_.
    
    - A **Data Package** names the sources.
    - A **Schema** states the contract (including nested fields).
    - A **Query** expresses the transformation and destination.
        
- **One promise:** keep data shaped as it is (nested stays nested), let SQL decide when to flatten, and push work down to sources when they can handle filters, limits, and projections.
    
- **One outcome:** teams use ordinary SQL to explore, combine, and materialize external data—fast enough for analysis, structured enough for governance—landing clean tables in the lake when needed.
    

weavETL is not a warehouse or an orchestrator; it’s the connective tissue that makes “query anything” feel native, repeatable, and auditable.

## Local setup

Projects are configured via a `weavetl_project.yaml` file at the root of your repository. A minimal configuration that enables the YAML connections backend looks like this:

```yaml
name: Example Project
connections:
  backends:
    - type: yaml
      path: connections/local.yaml
```

The referenced YAML file defines the actual connections. Here is a sample `connections/local.yaml` you can adapt:

```yaml
connections:
  - id: http.myapi
    type: http
    endpoint:
      baseUrl: https://api.example.com
    auth:
      kind: token
      token: my-api-token-value
      placement: header
      name: Authorization
      prefix: Bearer
    options:
      timeoutSeconds: 20
      retries: 5
```

Check these files into your project root (but keep the connections YAML out of version control if it contains secrets) and then use the `weavetl connections` CLI command to inspect what has been configured.