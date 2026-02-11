# Edge Optimizer Architecture

## System Overview

```mermaid
flowchart TB
    subgraph Orchestration["Orchestration Layer"]
        n8n["n8n<br/>Workflow Engine"]
        pw["Playwright<br/>Headless Browser"]
    end

    subgraph Security["4-Layer Security"]
        dns["DNS TXT Auth<br/>_eo-auth.domain"]
        cloud["Cloud Auth<br/>IAM/OAuth/CF-Access"]
        token["Token Verification<br/>SHA-256(URL+Secret)"]
        rate["Rate Control<br/>Sleep/Batch"]
    end

    subgraph RequestEngines["Request Engines (Serverless)"]
        direction LR
        subgraph AWS["AWS"]
            lambda1["Lambda<br/>ap-northeast-1"]
            lambda2["Lambda<br/>ap-southeast-1"]
            lambda3["Lambda<br/>us-east-1"]
        end
        subgraph Azure["Azure"]
            azfunc1["Functions<br/>japan-east"]
            azfunc2["Functions<br/>east-asia"]
        end
        subgraph GCP["GCP"]
            run1["Cloud Run<br/>asia-northeast1"]
            run2["Cloud Run<br/>asia-southeast1"]
        end
        subgraph CF["Cloudflare"]
            worker["Workers<br/>Global Edge"]
        end
    end

    subgraph CDN["Target CDN Edge Locations"]
        direction LR
        edge1["Tokyo Edge"]
        edge2["Singapore Edge"]
        edge3["US Edge"]
        edge4["EU Edge"]
    end

    subgraph Target["Target Web Application"]
        origin["Origin Server"]
    end

    subgraph Output["Output"]
        csv["CSV Report"]
        json["JSON Data"]
    end

    n8n --> pw
    pw --> |"Asset URLs<br/>Extraction"| n8n
    n8n --> Security
    Security --> RequestEngines

    lambda1 --> edge1
    lambda2 --> edge2
    azfunc1 --> edge1
    azfunc2 --> edge2
    run1 --> edge1
    run2 --> edge2
    worker --> edge1 & edge2 & edge3 & edge4

    edge1 & edge2 & edge3 & edge4 --> origin

    RequestEngines --> |"Response<br/>Headers/Metrics"| n8n
    n8n --> Output

    classDef orchestration fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef security fill:#ffd43b,stroke:#fab005,color:#000
    classDef aws fill:#ff9900,stroke:#cc7a00,color:#fff
    classDef azure fill:#0078d4,stroke:#005a9e,color:#fff
    classDef gcp fill:#4285f4,stroke:#2a6acf,color:#fff
    classDef cf fill:#f38020,stroke:#c56a1a,color:#fff
    classDef cdn fill:#20c997,stroke:#12b886,color:#fff
    classDef output fill:#748ffc,stroke:#4c6ef5,color:#fff

    class n8n,pw orchestration
    class dns,cloud,token,rate security
    class lambda1,lambda2,lambda3 aws
    class azfunc1,azfunc2 azure
    class run1,run2 gcp
    class worker cf
    class edge1,edge2,edge3,edge4 cdn
    class csv,json output
```

## Request Flow Sequence

```mermaid
sequenceDiagram
    autonumber
    participant n8n as n8n Orchestrator
    participant PW as Playwright
    participant DNS as DNS Server
    participant RE as Request Engine<br/>(Lambda/Functions/Run/Workers)
    participant CDN as CDN Edge
    participant Origin as Origin Server

    rect rgb(255, 107, 107, 0.1)
        Note over n8n,PW: Step.0 - URL Discovery
        n8n->>DNS: Verify _eo-auth.domain TXT
        DNS-->>n8n: eo-authorized-token
        n8n->>n8n: XML Sitemap Parse
    end

    rect rgb(32, 201, 151, 0.1)
        Note over n8n,PW: Step.1 - Asset Extraction
        n8n->>PW: Load Main Document
        PW->>PW: Execute JavaScript
        PW-->>n8n: All Asset URLs (CSS/JS/IMG/Font)
        n8n->>n8n: Filter & Classify URLs
        n8n->>n8n: Assign User-Agent Variants
        n8n->>n8n: Generate SHA-256 Tokens
    end

    rect rgb(255, 212, 59, 0.1)
        Note over n8n,RE: Step.2 - GEO Distributed Request
        loop For Each URL × Variant × Region
            n8n->>RE: POST {targetUrl, token, headers}
            RE->>RE: Verify Token (SHA-256)
            RE->>CDN: GET with User-Agent/Accept-Language
            CDN->>Origin: Cache MISS → Fetch
            Origin-->>CDN: Response + Cache-Control
            CDN-->>RE: Response + Cache Headers
            RE-->>n8n: {headers, metrics, security}
        end
    end

    rect rgb(116, 143, 252, 0.1)
        Note over n8n: Step.3 - Output
        n8n->>n8n: Flatten JSON
        n8n->>n8n: Export CSV/JSON
    end
```

## 4-Layer Security Model

```mermaid
flowchart LR
    subgraph Layer1["Layer 1: Domain Ownership"]
        dns["DNS TXT Record<br/>_eo-auth.example.com"]
    end

    subgraph Layer2["Layer 2: Cloud Authentication"]
        iam["AWS IAM<br/>Access Key"]
        azkey["Azure<br/>Function Key"]
        oauth["GCP OAuth2<br/>Service Account"]
        cfaccess["Cloudflare<br/>Access Token"]
    end

    subgraph Layer3["Layer 3: Token Verification"]
        token["SHA-256<br/>Hash(URL + Secret)"]
    end

    subgraph Layer4["Layer 4: Rate Control"]
        sleep["Random Sleep<br/>1000-3999ms"]
        batch["Batch Processing<br/>Loop Control"]
    end

    Layer1 --> Layer2 --> Layer3 --> Layer4

    classDef l1 fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef l2 fill:#ffd43b,stroke:#fab005,color:#000
    classDef l3 fill:#20c997,stroke:#12b886,color:#fff
    classDef l4 fill:#748ffc,stroke:#4c6ef5,color:#fff

    class dns l1
    class iam,azkey,oauth,cfaccess l2
    class token l3
    class sleep,batch l4
```

## Data Flow & Variant Expansion

```mermaid
flowchart LR
    subgraph Input["Input"]
        sitemap["XML Sitemap<br/>100 URLs"]
    end

    subgraph Extraction["Asset Extraction"]
        pw["Playwright<br/>+500 Assets"]
    end

    subgraph Variants["Variant Expansion"]
        ua["User-Agent<br/>×2 variants"]
        lang["Accept-Language<br/>×2 languages"]
        region["Regions<br/>×4 clouds"]
    end

    subgraph Total["Total Requests"]
        calc["600 URLs<br/>× 2 UA<br/>× 2 Lang<br/>× 4 Regions<br/>= 9,600 Requests"]
    end

    subgraph Output["Output Data"]
        headers["Response Headers<br/>Cache-Control, Vary, CDN"]
        metrics["Performance Metrics<br/>TTFB, Response Time"]
        security["Security Headers<br/>CSP, HSTS, X-Frame"]
    end

    Input --> Extraction --> Variants --> Total --> Output

    classDef input fill:#e7f5ff,stroke:#339af0,color:#000
    classDef process fill:#fff3bf,stroke:#fcc419,color:#000
    classDef output fill:#d3f9d8,stroke:#40c057,color:#000

    class sitemap input
    class pw,ua,lang,region process
    class calc process
    class headers,metrics,security output
```

## n8n Workflow Node Structure

```mermaid
flowchart TB
    subgraph Step0["Step.0 (#001-099)<br/>URL Discovery"]
        n010["#010 Starter<br/>XML Sitemap"]
        n015["#015 DNS Fetch"]
        n020["#020 DNS Auth"]
    end

    subgraph Step1["Step.1 (#100-199)<br/>Asset Extraction & Setup"]
        n140["#140 Playwright<br/>Asset Extract"]
        n155["#155 URL Filter"]
        n160["#160 Classify<br/>main/asset/exception"]
        n170["#170 Token Gen<br/>SHA-256"]
        n175["#175 User-Agent<br/>Assignment"]
        n180["#180 RequestEngine<br/>Settings"]
    end

    subgraph Step2["Step.2 (#200-399)<br/>GEO Distributed Request"]
        n220["#220 Loop<br/>Batch Control"]
        n225["#225 Switcher<br/>Cloud Router"]
        n280aws["#280 AWS<br/>Lambda"]
        n280az["#280 Azure<br/>Functions"]
        n280gcp["#280 GCP<br/>Cloud Run"]
        n280cf["#280 CF<br/>Workers"]
        n340["#340 Sleep<br/>Rate Control"]
    end

    subgraph Step3["Step.3 (#400+)<br/>Output"]
        n350["#350 JSON<br/>Flattener"]
        n420["#420 CSV<br/>Export"]
    end

    n010 --> n015 --> n020
    n020 --> n140 --> n155 --> n160 --> n170 --> n175 --> n180
    n180 --> n220 --> n225
    n225 --> n280aws & n280az & n280gcp & n280cf
    n280aws & n280az & n280gcp & n280cf --> n340
    n340 --> n220
    n220 --> n350 --> n420

    classDef step0 fill:#ffe3e3,stroke:#fa5252,color:#000
    classDef step1 fill:#fff3bf,stroke:#fcc419,color:#000
    classDef step2 fill:#d3f9d8,stroke:#40c057,color:#000
    classDef step3 fill:#d0ebff,stroke:#339af0,color:#000

    class n010,n015,n020 step0
    class n140,n155,n160,n170,n175,n180 step1
    class n220,n225,n280aws,n280az,n280gcp,n280cf,n340 step2
    class n350,n420 step3
```

## Request Engine Response Schema

```mermaid
classDiagram
    class Response {
        +headers.general.*
        +headers.request-headers.*
        +headers.response-headers.*
        +eo.meta.*
        +eo.measure.*
        +eo.performance.*
        +eo.security.*
    }

    class GeneralHeaders {
        +url: string
        +method: string
        +statusCode: number
        +statusText: string
    }

    class RequestHeaders {
        +User-Agent: string
        +Accept-Language: string
    }

    class ResponseHeaders {
        +cache-control: string
        +vary: string
        +cf-ray: string
        +x-amz-cf-id: string
        +x-azure-ref: string
    }

    class EOMetadata {
        +httpRequestNumber: number
        +httpRequestUUID: string
        +httpRequestRoundID: string
        +cloud_type_area: string
        +urltype: string
    }

    class EOMeasure {
        +ttfb: number
        +responseTime: number
        +contentLength: number
    }

    class EOPerformance {
        +cacheStatus: string
        +cdnProvider: string
        +edgeLocation: string
    }

    class EOSecurity {
        +csp: boolean
        +hsts: boolean
        +xFrameOptions: string
        +xContentTypeOptions: string
    }

    Response --> GeneralHeaders
    Response --> RequestHeaders
    Response --> ResponseHeaders
    Response --> EOMetadata
    Response --> EOMeasure
    Response --> EOPerformance
    Response --> EOSecurity
```

## Multi-Cloud Deployment

```mermaid
flowchart TB
    subgraph GitHub["GitHub Repository"]
        code["Request Engine<br/>Source Code"]
        actions["GitHub Actions<br/>CI/CD"]
    end

    subgraph IaC["Infrastructure as Code"]
        cfn["CloudFormation<br/>(AWS)"]
        bicep["Bicep<br/>(Azure)"]
        gha["GitHub Actions<br/>(GCP/CF)"]
    end

    subgraph Secrets["Secret Management"]
        awssm["AWS<br/>Secrets Manager"]
        azkv["Azure<br/>Key Vault"]
        gcpsm["GCP<br/>Secret Manager"]
        cfenv["Cloudflare<br/>Environment"]
    end

    subgraph RequestEngines["Deployed Request Engines"]
        lambda["AWS Lambda"]
        azfunc["Azure Functions"]
        run["GCP Cloud Run"]
        worker["CF Workers"]
    end

    code --> actions
    actions --> cfn --> lambda
    actions --> bicep --> azfunc
    actions --> gha --> run & worker

    awssm --> lambda
    azkv --> azfunc
    gcpsm --> run
    cfenv --> worker

    classDef github fill:#24292e,stroke:#1b1f23,color:#fff
    classDef iac fill:#6f42c1,stroke:#5a32a3,color:#fff
    classDef secrets fill:#ffd43b,stroke:#fab005,color:#000
    classDef engines fill:#20c997,stroke:#12b886,color:#fff

    class code,actions github
    class cfn,bicep,gha iac
    class awssm,azkv,gcpsm,cfenv secrets
    class lambda,azfunc,run,worker engines
```

## Why Edge Optimizer?

```mermaid
mindmap
    root((Edge<br/>Optimizer))
        GEO Distributed
            AWS Lambda
            Azure Functions
            GCP Cloud Run
            CF Workers
            Any Region
        Full Asset Warmup
            Main Documents
            CSS/JS
            Images
            Fonts
            Dynamic Assets
        Variant Support
            User-Agent
            Accept-Language
            Custom Headers
        4-Layer Security
            DNS Auth
            Cloud Auth
            Token Verify
            Rate Control
        Multi-CDN Detection
            Cloudflare
            CloudFront
            Azure CDN
            Akamai
            Fastly
            Vercel
        Beyond Warmup
            Performance Metrics
            Security Audit
            Config Validation
            AI Data Collection
```
