/* API Base Detection: Auto-connects to FastAPI even when opened via file:/// or other ports */
    const API_BASE = (window.location.protocol === "http:" && window.location.port === "8000") 
      ? "" 
      : "http://127.0.0.1:8000";

    /* Client-side PDF text extractor */
    async function parsePdfClient(file) {
      if (window.pdfjsLib) {
        try {
          pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
          const buffer = await file.arrayBuffer();
          const pdf = await pdfjsLib.getDocument({ data: buffer }).promise;
          let fullText = "";
          for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const content = await page.getTextContent();
            fullText += content.items.map(item => item.str).join(" ") + "\n";
          }
          if (fullText.trim()) return fullText;
        } catch (err) {
          console.warn("PDF.js worker error, trying raw buffer scan:", err);
        }
      }
      try {
        const buffer = await file.arrayBuffer();
        const raw = new TextDecoder("latin1").decode(buffer);
        const matches = raw.match(/\(([^)]+)\)\s*Tj/g) || [];
        if (matches.length > 0) {
          return matches.map(m => m.slice(1, -3)).join(" ");
        }
      } catch (e) {}
      return "";
    }

    /* Client-side DOCX text extractor */
    async function parseDocxClient(file) {
      if (window.mammoth) {
        try {
          const buffer = await file.arrayBuffer();
          const result = await mammoth.extractRawText({ arrayBuffer: buffer });
          if (result.value && result.value.trim()) return result.value;
        } catch (err) {
          console.warn("Mammoth error, trying raw XML scan:", err);
        }
      }
      try {
        const buffer = await file.arrayBuffer();
        const raw = new TextDecoder("utf-8", { fatal: false }).decode(buffer);
        const matches = raw.match(/<w:t[^>]*>([^<]+)<\/w:t>/g) || [];
        if (matches.length > 0) {
          return matches.map(m => m.replace(/<[^>]+>/g, "")).join(" ");
        }
      } catch (e) {}
      return "";
    }

    /* Domain-tailored benchmark Job Description fallback */
    function getClientBenchmarkJd(jobTitle, resumeText) {
      const combined = `${jobTitle} ${resumeText.slice(0, 300)}`.toLowerCase();
      if (/data|ml|mle|ai|machine learning|analyst|vision|nlp/.test(combined)) {
        return "REQUIRED QUALIFICATIONS:\n- Strong programming experience in Python and SQL.\n- Practical expertise in Machine Learning, Pandas, NumPy, and Scikit-learn.\n- Experience designing data pipelines and performing exploratory data analysis.\n\nPREFERRED QUALIFICATIONS:\n- Deep Learning experience with PyTorch or TensorFlow.\n- Cloud platforms (AWS or GCP) and Docker containerization.\n- Git version control, CI/CD, and REST APIs.";
      }
      if (/devops|cloud|infra|sre|platform|kubernetes|docker|terraform/.test(combined)) {
        return "REQUIRED QUALIFICATIONS:\n- Hands-on Linux systems administration and Bash/Shell scripting.\n- Containerization and orchestration with Docker and Kubernetes.\n- Cloud infrastructure management with AWS or GCP.\n- Infrastructure as Code with Terraform and CI/CD automation.\n\nPREFERRED QUALIFICATIONS:\n- Python or Go automation scripting.\n- Observability, Nginx reverse proxy configuration, and System Design.";
      }
      if (/backend|api|server|microservices|java|node|django|fastapi/.test(combined)) {
        return "REQUIRED QUALIFICATIONS:\n- Production experience developing scalable REST APIs and microservices.\n- Proficiency in backend languages: Python, Node.js, Java, or Go.\n- Relational databases (PostgreSQL or MySQL) and query optimization.\n- Docker containerization and Git version control.\n\nPREFERRED QUALIFICATIONS:\n- In-memory caching with Redis and message brokers.\n- Cloud deployment on AWS and automated CI/CD pipelines.";
      }
      return "REQUIRED QUALIFICATIONS:\n- Foundations in modern programming: JavaScript, TypeScript, or Python.\n- Experience building applications with React, Node.js, FastAPI, or Django.\n- Working knowledge of SQL, database modeling, and REST APIs.\n- Git version control and collaborative development practices.\n\nPREFERRED QUALIFICATIONS:\n- Cloud infrastructure (AWS, GCP, or Azure).\n- Containerization with Docker and automated CI/CD workflows.";
    }

    /* =========================================================
       SkillGap AI - Complete Embedded Client Engine & Controller
       ========================================================= */

    // 1. Master Skill Taxonomy & Aliases
    const CATEGORY_META = {
      languages: { label: "Languages", color: "#3b82f6" },
      frontend: { label: "Frontend", color: "#ec4899" },
      backend: { label: "Backend", color: "#10b981" },
      databases: { label: "Databases & Storage", color: "#f59e0b" },
      cloud_devops: { label: "Cloud & DevOps", color: "#6366f1" },
      data_ai: { label: "Data & AI / ML", color: "#8b5cf6" },
      architecture_testing: { label: "Architecture & Practices", color: "#14b8a6" },
      soft_skills: { label: "Soft & Leadership Skills", color: "#f97316" }
    };

    const SYNONYM_MAP = {
      "python": "Python", "python3": "Python", "py": "Python",
      "javascript": "JavaScript", "js": "JavaScript", "ecmascript": "JavaScript", "es6": "JavaScript",
      "typescript": "TypeScript", "ts": "TypeScript",
      "golang": "Go", "go": "Go", "rust": "Rust",
      "java": "Java", "c++": "C++", "cpp": "C++", "c#": "C#", "csharp": "C#",
      "sql": "SQL", "bash": "Bash/Shell", "shell": "Bash/Shell", "html": "HTML5/CSS3", "css": "HTML5/CSS3", "html5": "HTML5/CSS3", "css3": "HTML5/CSS3",
      "c": "C", "c language": "C", "c programming": "C", "ansi c": "C", "embedded c": "C",
      "r": "R", "r programming": "R", "r language": "R", "r-lang": "R",
      "react": "React", "reactjs": "React", "react.js": "React",
      "next": "Next.js", "nextjs": "Next.js", "next.js": "Next.js",
      "vue": "Vue.js", "vuejs": "Vue.js", "angular": "Angular",
      "tailwind": "Tailwind CSS", "tailwindcss": "Tailwind CSS", "redux": "Redux", "websockets": "WebSockets", "websocket": "WebSockets",
      "bootstrap": "Bootstrap", "bootstrap 4": "Bootstrap", "bootstrap 5": "Bootstrap", "bootstrap css": "Bootstrap",
      "jquery": "jQuery",
      "ui/ux": "UI/UX Design", "ui/ux design": "UI/UX Design", "ui design": "UI/UX Design", "ux design": "UI/UX Design", "figma": "Figma",
      "node": "Node.js", "nodejs": "Node.js", "node.js": "Node.js",
      "fastapi": "FastAPI", "django": "Django", "flask": "Flask", "express": "Express.js", "expressjs": "Express.js",
      "spring boot": "Spring Boot", "graphql": "GraphQL", "grpc": "gRPC",
      "asp.net": "ASP.NET", "asp.net core": "ASP.NET", ".net core": "ASP.NET", "dotnet core": "ASP.NET", "aspnet": "ASP.NET",
      "laravel": "Laravel", "php laravel": "Laravel",
      "postgres": "PostgreSQL", "postgresql": "PostgreSQL", "psql": "PostgreSQL",
      "mysql": "MySQL", "mongo": "MongoDB", "mongodb": "MongoDB", "redis": "Redis", "elasticsearch": "Elasticsearch",
      "sql server": "SQL Server", "mssql": "SQL Server", "ms sql": "SQL Server", "microsoft sql server": "SQL Server",
      "oracle": "Oracle Database", "oracle db": "Oracle Database", "oracle database": "Oracle Database",
      "dbms": "DBMS", "rdbms": "DBMS", "database management": "DBMS",
      "docker": "Docker", "containerization": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
      "aws": "AWS", "gcp": "Google Cloud Platform (GCP)", "azure": "Microsoft Azure",
      "ci/cd": "CI/CD", "cicd": "CI/CD", "github actions": "GitHub Actions", "terraform": "Terraform", "linux": "Linux", "nginx": "Nginx",
      "machine learning": "Machine Learning", "ml": "Machine Learning", "deep learning": "Deep Learning",
      "natural language processing": "Natural Language Processing (NLP)", "nlp": "Natural Language Processing (NLP)",
      "pytorch": "PyTorch", "tensorflow": "TensorFlow", "pandas": "Pandas", "numpy": "NumPy", "scikit-learn": "Scikit-learn",
      "apache spark": "Apache Spark", "data pipelines": "Data Pipelines / ETL", "etl": "Data Pipelines / ETL",
      "data analysis": "Data Analysis", "data analytics": "Data Analysis", "exploratory data analysis": "Data Analysis", "eda": "Data Analysis",
      "excel": "Excel", "microsoft excel": "Excel", "ms excel": "Excel", "spreadsheets": "Excel", "spreadsheet": "Excel", "advanced excel": "Excel",
      "tableau": "Tableau", "power bi": "Power BI", "powerbi": "Power BI", "power-bi": "Power BI",
      "rest": "REST APIs", "rest api": "REST APIs", "restful": "REST APIs", "microservices": "Microservices",
      "system design": "System Design", "unit testing": "Unit Testing", "tdd": "Test-Driven Development (TDD)",
      "agile": "Agile/Scrum", "git": "Git", "github": "Git", "gitlab": "Git", "version control": "Git",
      "data structures": "Data Structures & Algorithms", "data structures and algorithms": "Data Structures & Algorithms", "data structures & algorithms": "Data Structures & Algorithms", "dsa": "Data Structures & Algorithms",
      "oop": "Object-Oriented Programming (OOP)", "oops": "Object-Oriented Programming (OOP)", "object-oriented programming": "Object-Oriented Programming (OOP)", "object oriented programming": "Object-Oriented Programming (OOP)",
      "software testing": "Software Testing & QA", "qa": "Software Testing & QA", "quality assurance": "Software Testing & QA", "manual testing": "Software Testing & QA", "automation testing": "Software Testing & QA", "selenium": "Software Testing & QA", "cypress": "Software Testing & QA", "pytest": "Software Testing & QA", "test cases": "Software Testing & QA",
      "operating systems": "Operating Systems", "computer networks": "Computer Networks", "networking": "Computer Networks", "tcp/ip": "Computer Networks",
      "problem solving": "Problem Solving", "problem-solving": "Problem Solving", "troubleshooting": "Problem Solving", "debugging": "Problem Solving",
      "communication": "Communication", "leadership": "Team Leadership", "mentorship": "Mentorship", "cross-functional collaboration": "Cross-functional Collaboration",
      "teamwork": "Teamwork & Collaboration", "team work": "Teamwork & Collaboration", "collaboration": "Teamwork & Collaboration",
      "time management": "Time Management", "prioritization": "Time Management",
      "adaptability": "Adaptability", "adaptable": "Adaptability", "flexible": "Adaptability",
      "analytical skills": "Analytical Thinking", "analytical thinking": "Analytical Thinking"
    };

    const MASTER_TAXONOMY = {
      "Python": { category: "languages", description: "High-level versatile programming language." },
      "JavaScript": { category: "languages", description: "Core dynamic language of the web platform." },
      "TypeScript": { category: "languages", description: "Typed superset of JavaScript with static types." },
      "Go": { category: "languages", description: "Statically typed language for concurrency." },
      "Rust": { category: "languages", description: "Systems language emphasizing memory safety." },
      "Java": { category: "languages", description: "Class-based object-oriented enterprise language." },
      "C++": { category: "languages", description: "High-performance systems programming language." },
      "C#": { category: "languages", description: "Modern language developed by Microsoft for .NET." },
      "C": { category: "languages", description: "Foundational procedural systems programming language." },
      "R": { category: "languages", description: "Statistical computing and graphics programming language." },
      "SQL": { category: "languages", description: "Standard query language for relational databases." },
      "Bash/Shell": { category: "languages", description: "Unix scripting and automation." },
      "HTML5/CSS3": { category: "languages", description: "Web layout and styling standards." },
      "React": { category: "frontend", description: "Declarative component-based UI library." },
      "Next.js": { category: "frontend", description: "Full-stack React framework with SSR and App Router." },
      "Vue.js": { category: "frontend", description: "Progressive JavaScript UI framework." },
      "Angular": { category: "frontend", description: "TypeScript-based enterprise UI platform." },
      "Tailwind CSS": { category: "frontend", description: "Utility-first CSS framework." },
      "Bootstrap": { category: "frontend", description: "Responsive front-end framework for mobile-first web development." },
      "jQuery": { category: "frontend", description: "Fast, feature-rich JavaScript DOM manipulation library." },
      "UI/UX Design": { category: "frontend", description: "User interface design, wireframing, and user experience." },
      "Figma": { category: "frontend", description: "Collaborative cloud-based interface design tool." },
      "Redux": { category: "frontend", description: "Predictable state container for web apps." },
      "WebSockets": { category: "frontend", description: "Real-time bidirectional communication protocol." },
      "Node.js": { category: "backend", description: "Asynchronous JavaScript server runtime." },
      "FastAPI": { category: "backend", description: "High-performance Python API framework." },
      "Django": { category: "backend", description: "Batteries-included Python web framework." },
      "Flask": { category: "backend", description: "Lightweight Python micro-framework." },
      "Express.js": { category: "backend", description: "Fast, minimalist web framework for Node.js." },
      "Spring Boot": { category: "backend", description: "Enterprise Java microservices framework." },
      "ASP.NET": { category: "backend", description: "Microsoft framework for modern web applications." },
      "Laravel": { category: "backend", description: "Expressive PHP web application framework." },
      "GraphQL": { category: "backend", description: "Declarative data querying API specification." },
      "gRPC": { category: "backend", description: "Universal RPC framework engineered by Google." },
      "PostgreSQL": { category: "databases", description: "Advanced relational ACID database." },
      "MySQL": { category: "databases", description: "Popular open-source relational database." },
      "MongoDB": { category: "databases", description: "Document-oriented NoSQL database." },
      "Redis": { category: "databases", description: "In-memory caching and message broker." },
      "Elasticsearch": { category: "databases", description: "Distributed search and analytics engine." },
      "SQL Server": { category: "databases", description: "Microsoft relational database management system." },
      "Oracle Database": { category: "databases", description: "Enterprise multi-model database management system." },
      "DBMS": { category: "databases", description: "Database management systems and relational schema design." },
      "Docker": { category: "cloud_devops", description: "Application containerization platform." },
      "Kubernetes": { category: "cloud_devops", description: "Automated container orchestration system." },
      "AWS": { category: "cloud_devops", description: "Amazon Web Services cloud platform." },
      "Google Cloud Platform (GCP)": { category: "cloud_devops", description: "Google suite of cloud computing services." },
      "Microsoft Azure": { category: "cloud_devops", description: "Microsoft cloud platform." },
      "CI/CD": { category: "cloud_devops", description: "Continuous integration & continuous delivery." },
      "GitHub Actions": { category: "cloud_devops", description: "Workflow automation directly in GitHub." },
      "Terraform": { category: "cloud_devops", description: "Infrastructure as Code declarative tool." },
      "Linux": { category: "cloud_devops", description: "Unix-like operating system powering infrastructure." },
      "Nginx": { category: "cloud_devops", description: "High-performance HTTP server & reverse proxy." },
      "Machine Learning": { category: "data_ai", description: "Predictive mathematical models from data." },
      "Deep Learning": { category: "data_ai", description: "Multi-layered artificial neural networks." },
      "Natural Language Processing (NLP)": { category: "data_ai", description: "Computational linguistics and NLP models." },
      "PyTorch": { category: "data_ai", description: "Deep learning framework by Meta." },
      "TensorFlow": { category: "data_ai", description: "Machine learning platform by Google." },
      "Pandas": { category: "data_ai", description: "Data manipulation and analysis library." },
      "NumPy": { category: "data_ai", description: "Scientific computing and array operations." },
      "Scikit-learn": { category: "data_ai", description: "Classical machine learning in Python." },
      "Apache Spark": { category: "data_ai", description: "Distributed big data computing engine." },
      "Data Pipelines / ETL": { category: "data_ai", description: "Data extraction, transformation & loading." },
      "Data Analysis": { category: "data_ai", description: "Data inspection, transformation, and insight discovery." },
      "Excel": { category: "data_ai", description: "Spreadsheet modeling, formulas, and data analysis." },
      "Tableau": { category: "data_ai", description: "Interactive data visualization and reporting software." },
      "Power BI": { category: "data_ai", description: "Microsoft interactive business analytics platform." },
      "REST APIs": { category: "architecture_testing", description: "Architectural style for web services." },
      "Microservices": { category: "architecture_testing", description: "Modular independent service architecture." },
      "System Design": { category: "architecture_testing", description: "Large-scale distributed systems architecture." },
      "Unit Testing": { category: "architecture_testing", description: "Automated component-level test isolation." },
      "Test-Driven Development (TDD)": { category: "architecture_testing", description: "Test-first software development cycle." },
      "Agile/Scrum": { category: "architecture_testing", description: "Iterative agile product sprint management." },
      "Git": { category: "architecture_testing", description: "Distributed version control system." },
      "Data Structures & Algorithms": { category: "architecture_testing", description: "Foundational computing structures and algorithmic design." },
      "Object-Oriented Programming (OOP)": { category: "architecture_testing", description: "Objects, encapsulation, inheritance, and polymorphism." },
      "Software Testing & QA": { category: "architecture_testing", description: "Quality assurance, manual and automated verification." },
      "Operating Systems": { category: "architecture_testing", description: "Core OS principles, processes, and memory management." },
      "Computer Networks": { category: "architecture_testing", description: "Networking protocols, TCP/IP stack, and HTTP/HTTPS." },
      "Problem Solving": { category: "soft_skills", description: "Analytical problem deconstruction." },
      "Communication": { category: "soft_skills", description: "Clear verbal and written collaboration." },
      "Team Leadership": { category: "soft_skills", description: "Guiding and empowering engineering teams." },
      "Mentorship": { category: "soft_skills", description: "Coaching engineers and code reviews." },
      "Cross-functional Collaboration": { category: "soft_skills", description: "Partnering with product and design." },
      "Teamwork & Collaboration": { category: "soft_skills", description: "Working productively within engineering teams." },
      "Time Management": { category: "soft_skills", description: "Prioritizing tasks and meeting deadlines." },
      "Adaptability": { category: "soft_skills", description: "Quickly mastering new technologies and pivoting." },
      "Analytical Thinking": { category: "soft_skills", description: "Systematic breakdown of complex problems." }
    };

    const PREREQUISITES_DAG = {
      "TypeScript": ["JavaScript"],
      "React": ["JavaScript", "HTML5/CSS3"],
      "Next.js": ["React", "JavaScript", "TypeScript"],
      "Vue.js": ["JavaScript", "HTML5/CSS3"],
      "Angular": ["TypeScript", "JavaScript"],
      "Node.js": ["JavaScript"],
      "FastAPI": ["Python"],
      "Django": ["Python", "SQL"],
      "Docker": ["Linux", "Bash/Shell"],
      "Kubernetes": ["Docker", "Linux"],
      "CI/CD": ["Git", "Bash/Shell"],
      "Terraform": ["Linux", "AWS"],
      "Machine Learning": ["Python", "NumPy", "Pandas", "Scikit-learn"],
      "Deep Learning": ["Machine Learning", "Python"],
      "PyTorch": ["Deep Learning", "Python"],
      "PostgreSQL": ["SQL"],
      "Microservices": ["REST APIs", "Docker"],
      "Bootstrap": ["HTML5/CSS3"],
      "jQuery": ["JavaScript"],
      "UI/UX Design": ["HTML5/CSS3"],
      "ASP.NET": ["C#"],
      "Laravel": ["PHP"],
      "Data Analysis": ["Python", "SQL"],
      "Power BI": ["Excel"],
      "Tableau": ["SQL"],
      "Data Structures & Algorithms": ["Object-Oriented Programming (OOP)"],
      "Software Testing & QA": ["Unit Testing"]
    };

    const SKILL_RESOURCES = {
      "JavaScript": { hours: 25, diff: "Beginner", doc: "https://developer.mozilla.org/en-US/docs/Web/JavaScript", proj: "Build an interactive event-driven state store." },
      "TypeScript": { hours: 15, diff: "Intermediate", doc: "https://www.typescriptlang.org/docs/", proj: "Refactor a JavaScript codebase with strict generics." },
      "React": { hours: 30, diff: "Intermediate", doc: "https://react.dev/", proj: "Build a responsive dashboard with custom hooks and memoization." },
      "Next.js": { hours: 20, diff: "Intermediate", doc: "https://nextjs.org/learn", proj: "Deploy a fullstack SaaS with App Router and Server Actions." },
      "Node.js": { hours: 20, diff: "Intermediate", doc: "https://nodejs.org/en/docs", proj: "Construct an asynchronous REST API with JWT security." },
      "FastAPI": { hours: 18, diff: "Intermediate", doc: "https://fastapi.tiangolo.com/", proj: "Build a high-throughput async microservice with OpenAPI docs." },
      "Docker": { hours: 15, diff: "Intermediate", doc: "https://docs.docker.com/get-started/", proj: "Containerize a multi-tier web application with multi-stage builds." },
      "Kubernetes": { hours: 35, diff: "Advanced", doc: "https://kubernetes.io/docs/tutorials/", proj: "Deploy an autoscaling cluster with rolling zero-downtime releases." },
      "AWS": { hours: 30, diff: "Intermediate", doc: "https://explore.skillbuilder.aws/", proj: "Deploy serverless backend with Lambda, API Gateway, and S3." },
      "PostgreSQL": { hours: 20, diff: "Intermediate", doc: "https://www.postgresql.org/docs/", proj: "Design and benchmark a normalized database schema." },
      "Machine Learning": { hours: 40, diff: "Intermediate", doc: "https://scikit-learn.org/stable/", proj: "Train and evaluate an ensemble classification model." },
      "PyTorch": { hours: 35, diff: "Advanced", doc: "https://pytorch.org/tutorials/", proj: "Train a custom neural network on GPU for text or image classification." },
      "REST APIs": { hours: 12, diff: "Intermediate", doc: "https://restfulapi.net/", proj: "Design RESTful resources adhering strictly to RFC specifications." }
    };

    // Curated Company Openings Catalog
    const COMPANY_JOB_CATALOG = [
      {
        company: "Vercel",
        logo: "▲",
        color: "#000000",
        role: "Full-Stack / Frontend Engineer (Next.js & React)",
        domain: "frontend",
        loc: "Remote (Global)",
        salary: "$140k - $190k",
        req: ["React", "Next.js", "TypeScript", "JavaScript", "Tailwind CSS"],
        pref: ["Node.js", "WebSockets", "REST APIs"],
        apply: "https://vercel.com/careers",
        desc: "Build high-performance web experiences and developer tooling for Vercel's Next.js and frontend cloud platform."
      },
      {
        company: "Stripe",
        logo: "S",
        color: "#6366f1",
        role: "Full-Stack Software Engineer (Merchant Platform)",
        domain: "frontend",
        loc: "Remote / San Francisco, CA",
        salary: "$160k - $220k",
        req: ["JavaScript", "TypeScript", "React", "Node.js", "REST APIs"],
        pref: ["PostgreSQL", "Docker", "Git"],
        apply: "https://stripe.com/jobs",
        desc: "Architect the global economic infrastructure and dashboard tooling powering millions of online businesses."
      },
      {
        company: "Shopify",
        logo: "🛍️",
        color: "#95bf47",
        role: "Senior Web Developer (Storefront Platform)",
        domain: "frontend",
        loc: "Remote (US / Canada)",
        salary: "$135k - $185k",
        req: ["React", "JavaScript", "TypeScript", "HTML5/CSS3", "Redux"],
        pref: ["GraphQL", "REST APIs", "Unit Testing"],
        apply: "https://www.shopify.com/careers",
        desc: "Empower independent commerce globally by developing accessible storefronts and merchant interfaces."
      },
      {
        company: "Amazon Web Services (AWS)",
        logo: "A",
        color: "#ff9900",
        role: "Software Development Engineer II (Cloud Services)",
        domain: "backend",
        loc: "Seattle, WA / Austin, TX / Remote",
        salary: "$150k - $210k",
        req: ["Python", "Java", "SQL", "REST APIs", "System Design"],
        pref: ["Docker", "AWS", "Microservices", "PostgreSQL"],
        apply: "https://www.amazon.jobs/",
        desc: "Scale distributed, fault-tolerant backend infrastructure serving billions of requests per minute across AWS services."
      },
      {
        company: "Datadog",
        logo: "🐶",
        color: "#632ca6",
        role: "Backend Software Engineer (Platform Infrastructure)",
        domain: "backend",
        loc: "New York, NY / Remote",
        salary: "$155k - $205k",
        req: ["Python", "Go", "PostgreSQL", "Redis", "Linux"],
        pref: ["Docker", "Kubernetes", "Microservices"],
        apply: "https://www.datadoghq.com/careers/",
        desc: "Design ultra-low latency observability pipelines and real-time metric ingestion platforms."
      },
      {
        company: "Microsoft",
        logo: "⊞",
        color: "#00a4ef",
        role: "Software Engineer (Azure Core Backend)",
        domain: "backend",
        loc: "Redmond, WA / Remote",
        salary: "$145k - $195k",
        req: ["C#", "Python", "SQL", "REST APIs", "Unit Testing"],
        pref: ["Microsoft Azure", "Docker", "Microservices"],
        apply: "https://careers.microsoft.com/",
        desc: "Build resilient core cloud services and API gateways supporting enterprise mission-critical workloads on Azure."
      },
      {
        company: "OpenAI",
        logo: "✦",
        color: "#10a37f",
        role: "Machine Learning Engineer (Inference & Training)",
        domain: "data_ai",
        loc: "San Francisco, CA / Remote",
        salary: "$200k - $320k",
        req: ["Python", "PyTorch", "NumPy", "Pandas", "Machine Learning"],
        pref: ["Deep Learning", "Large Language Models (LLMs)", "Docker", "Linux"],
        apply: "https://openai.com/careers",
        desc: "Research, scale, and deploy foundational AI systems and transformer architectures."
      },
      {
        company: "Google DeepMind",
        logo: "G",
        color: "#4285f4",
        role: "Applied Machine Learning Specialist",
        domain: "data_ai",
        loc: "Mountain View, CA / New York, NY",
        salary: "$175k - $250k",
        req: ["Python", "TensorFlow", "PyTorch", "Machine Learning", "SQL"],
        pref: ["Natural Language Processing (NLP)", "Computer Vision", "Scikit-learn"],
        apply: "https://careers.google.com/",
        desc: "Bridge foundational intelligence research with real-world applications across multimodal models."
      },
      {
        company: "Snowflake",
        logo: "❄",
        color: "#29b5e8",
        role: "Data Platform Engineer (ETL & Query Optimization)",
        domain: "data_ai",
        loc: "San Mateo, CA / Remote",
        salary: "$150k - $210k",
        req: ["Python", "SQL", "Pandas", "Data Pipelines / ETL", "Apache Spark"],
        pref: ["PostgreSQL", "AWS", "Docker"],
        apply: "https://www.snowflake.com/careers/",
        desc: "Construct scalable cloud data warehousing pipelines handling petabytes of analytical queries per day."
      },
      {
        company: "HashiCorp",
        logo: "H",
        color: "#000000",
        role: "Cloud Infrastructure & Platform Engineer (Terraform)",
        domain: "cloud_devops",
        loc: "Remote (US / EMEA)",
        salary: "$145k - $195k",
        req: ["Terraform", "Docker", "Kubernetes", "Linux", "AWS"],
        pref: ["CI/CD", "GitHub Actions", "Go", "Bash/Shell"],
        apply: "https://www.hashicorp.com/careers",
        desc: "Empower automated multi-cloud provisioning and infrastructure workflows across enterprise environments."
      },
      {
        company: "Cloudflare",
        logo: "☁",
        color: "#f38020",
        role: "DevOps & Cloud Systems Engineer",
        domain: "cloud_devops",
        loc: "Austin, TX / San Francisco, CA / Remote",
        salary: "$140k - $190k",
        req: ["Linux", "Docker", "CI/CD", "Nginx", "Bash/Shell"],
        pref: ["Kubernetes", "Go", "Terraform", "Rust"],
        apply: "https://www.cloudflare.com/careers/",
        desc: "Help build a better internet by optimizing edge routing, DDoS mitigation, and global edge container runtimes."
      },
      {
        company: "GitLab",
        logo: "🦊",
        color: "#fc6d26",
        role: "Site Reliability & CI/CD Infrastructure Engineer",
        domain: "cloud_devops",
        loc: "All-Remote",
        salary: "$130k - $180k",
        req: ["CI/CD", "Git", "Kubernetes", "Docker", "Linux"],
        pref: ["Terraform", "Google Cloud Platform (GCP)", "Python"],
        apply: "https://about.gitlab.com/jobs/",
        desc: "Drive 99.99% availability and build scalable CI runner orchestration for millions of active software projects."
      }
    ];

    const SAMPLE_PRESETS = [
      {
        label: "Frontend -> Full-Stack",
        candidate: "Alex Chen (Frontend Specialist)",
        job: "Senior Full-Stack Engineer (Next.js / Node / PostgreSQL)",
        resume: `ALEX CHEN\nFrontend Developer with 3+ years experience in React, JavaScript, HTML5/CSS3, and Tailwind CSS.\nSkills: JavaScript, React, Tailwind CSS, Redux, Git, WebSockets, Unit Testing, Problem Solving.\nExperience building single-page apps and collaborating with product teams in Agile/Scrum sprints.`,
        jd: `REQUIRED QUALIFICATIONS:\n- 4+ years software engineering experience in JavaScript and TypeScript.\n- Deep hands-on proficiency with React and Next.js.\n- Strong backend experience building REST APIs with Node.js and Express.js.\n- Database modeling and query optimization in PostgreSQL.\n- Unit Testing, Git, and Agile/Scrum.\n\nPREFERRED QUALIFICATIONS:\n- Experience containerizing microservices with Docker.\n- Deployment to AWS cloud and CI/CD pipelines.`
      },
      {
        label: "Data Analyst -> ML Engineer",
        candidate: "Maya Patel (Data Analyst)",
        job: "Machine Learning Engineer (NLP & Deep Learning)",
        resume: `MAYA PATEL\nData Analyst with 2+ years experience in Python, SQL, Pandas, NumPy, and Tableau.\nExtracted and analyzed transactional data in PostgreSQL.\nStrong in Problem Solving, Communication, and exploratory data analysis.`,
        jd: `REQUIRED QUALIFICATIONS:\n- Strong Python programming with Pandas and NumPy.\n- Experience with classical Machine Learning algorithms and Scikit-learn.\n- Deep Learning neural networks using PyTorch or TensorFlow.\n- Solid SQL proficiency and version control with Git.\n\nPREFERRED QUALIFICATIONS:\n- Experience with Docker and model deployment on AWS.\n- Natural Language Processing (NLP) or Computer Vision.\n- Data Pipelines / ETL experience.`
      },
      {
        label: "Backend -> Cloud DevOps",
        candidate: "Jordan Rivera (Backend Dev)",
        job: "DevOps & Cloud Infrastructure Architect",
        resume: `JORDAN RIVERA\nBackend Software Engineer with 3 years building web services in Python, Django, and REST APIs.\nExperience with PostgreSQL, Redis, Linux Ubuntu, and Docker.\nStrong analytical thinking and Unit Testing.`,
        jd: `REQUIRED QUALIFICATIONS:\n- 3+ years infrastructure experience in Linux environments.\n- Container orchestration with Docker and Kubernetes.\n- Cloud infrastructure on AWS (VPC, IAM, EKS, S3).\n- Infrastructure as Code with Terraform.\n- CI/CD automation with GitHub Actions.\n\nPREFERRED QUALIFICATIONS:\n- Python or Go scripting.\n- Nginx reverse proxies and System Design.`
      }
    ];

    // Client-side NLP extraction
    function clientExtractSkills(text) {
      if (!text) return {};
      const found = {};
      const lower = text.toLowerCase();
      const terms = Object.keys(SYNONYM_MAP).sort((a, b) => b.length - a.length);

      terms.forEach(term => {
        let pattern;
        if (["c++", "c#", ".net", "ci/cd", "node.js", "next.js", "vue.js", "asp.net", "power-bi"].includes(term)) {
          pattern = new RegExp("(?:^|[^a-zA-Z0-9])" + term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + "(?![a-zA-Z0-9])", "gi");
        } else if (term === "c") {
          pattern = new RegExp("(?:^|[^a-zA-Z0-9])c(?![a-zA-Z0-9+#])", "gi");
        } else if (term === "r") {
          pattern = new RegExp("(?:^|[^a-zA-Z0-9])r(?![a-zA-Z0-9])", "gi");
        } else {
          pattern = new RegExp("\\b" + term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + "\\b", "gi");
        }

        const matches = lower.match(pattern);
        if (matches) {
          const canonical = SYNONYM_MAP[term];
          const meta = MASTER_TAXONOMY[canonical] || { category: "languages", description: "Technical competency" };
          if (!found[canonical]) {
            found[canonical] = {
              name: canonical,
              category: meta.category,
              category_label: CATEGORY_META[meta.category]?.label || meta.category,
              description: meta.description,
              count: matches.length
            };
          }
        }
      });
      return found;
    }

    // Client-side Cosine Similarity
    function clientCosineSimilarity(t1, t2) {
      const words = str => str.toLowerCase().match(/\b[a-zA-Z0-9_+#.-]{2,}\b/g) || [];
      const w1 = words(t1), w2 = words(t2);
      const freq = (list) => {
        const counts = {};
        list.forEach(w => counts[w] = (counts[w] || 0) + 1);
        return counts;
      };
      const f1 = freq(w1), f2 = freq(w2);
      const all = new Set([...Object.keys(f1), ...Object.keys(f2)]);

      let dot = 0, n1 = 0, n2 = 0;
      all.forEach(w => {
        const v1 = f1[w] || 0;
        const v2 = f2[w] || 0;
        dot += v1 * v2;
        n1 += v1 * v1;
        n2 += v2 * v2;
      });

      if (n1 === 0 || n2 === 0) return 0;
      return dot / (Math.sqrt(n1) * Math.sqrt(n2));
    }

    // Client-side Job Matcher
    function clientFindMatchingJobs(resumeText) {
      const resumeSkills = clientExtractSkills(resumeText);
      const candSkills = new Set(Object.keys(resumeSkills));

      const scored = COMPANY_JOB_CATALOG.map(job => {
        const req = new Set(job.req);
        const pref = new Set(job.pref || []);
        const matchedReq = [...req].filter(s => candSkills.has(s));
        const matchedPref = [...pref].filter(s => candSkills.has(s));
        const allMatched = [...matchedReq, ...matchedPref];
        const missingReq = [...req].filter(s => !candSkills.has(s));

        const total = (req.size * 2) + pref.size;
        const actual = (matchedReq.length * 2) + matchedPref.length;
        const pct = total > 0 ? Math.round((actual / total) * 100) : 50;

        const q = encodeURIComponent(`${job.role} ${allMatched.slice(0, 3).join(" ")}`.trim());
        const portal_links = {
          linkedin: `https://www.linkedin.com/jobs/search/?keywords=${q}&location=Remote&f_TPR=r604800&sortBy=DD`,
          google_jobs: `https://www.google.com/search?ibp=htl;jobs&q=${q}+Remote`,
          indeed: `https://www.indeed.com/jobs?q=${q}&l=Remote&fromage=7`,
          wellfound: `https://wellfound.com/jobs?role=${encodeURIComponent(job.role)}`,
          remoteok: `https://remoteok.com/remote-${encodeURIComponent(job.role.toLowerCase().replace(/[^a-z0-9]/g, "-"))}-jobs`
        };

        return {
          company: job.company,
          company_logo: job.logo,
          company_color: job.color,
          role_title: job.role,
          location: job.loc,
          salary_range: job.salary,
          description: job.desc,
          match_pct: Math.min(100, pct + 5),
          matched_skills: allMatched,
          missing_skills: missingReq,
          direct_apply_url: job.apply,
          portal_links: portal_links
        };
      });

      scored.sort((a, b) => b.match_pct - a.match_pct);
      const topJobs = scored.slice(0, 6);

      const topTitle = topJobs[0]?.role_title?.split("(")[0]?.trim() || "Software Engineer";
      const qGlobal = encodeURIComponent(`${topTitle} ${[...candSkills].slice(0, 3).join(" ")}`.trim());

      return {
        recommended_jobs: topJobs,
        global_portal_links: {
          linkedin: `https://www.linkedin.com/jobs/search/?keywords=${qGlobal}&location=Remote&f_TPR=r604800&sortBy=DD`,
          google_jobs: `https://www.google.com/search?ibp=htl;jobs&q=${qGlobal}+Remote`,
          indeed: `https://www.indeed.com/jobs?q=${qGlobal}&l=Remote&fromage=7`,
          wellfound: `https://wellfound.com/jobs?role=${encodeURIComponent(topTitle)}`,
          remoteok: `https://remoteok.com/remote-${encodeURIComponent(topTitle.toLowerCase().replace(/[^a-z0-9]/g, "-"))}-jobs`
        }
      };
    }

    // Client-side Gap Analysis & Topological Roadmap
    function runClientAnalysis(resumeText, jdText, candidateName, jobTitle) {
      let finalJdText = (jdText || "").trim();
      let jdSkills = clientExtractSkills(finalJdText);
      const resumeSkills = clientExtractSkills(resumeText);

      // Auto-benchmark if target job description had no recognized skills
      if (Object.keys(jdSkills).length === 0) {
        finalJdText = getClientBenchmarkJd(jobTitle, resumeText);
        jdSkills = clientExtractSkills(finalJdText);
      }

      const lowerJd = finalJdText.toLowerCase();
      const prefIdx = lowerJd.indexOf("preferred");

      const matched = [], missingReq = [], missingPref = [], additional = [];
      let totalWeight = 0, matchedWeight = 0;

      Object.keys(jdSkills).forEach(name => {
        const skill = jdSkills[name];
        const isPref = prefIdx !== -1 && lowerJd.indexOf(name.toLowerCase()) > prefIdx;
        const weight = isPref ? 1.0 : 2.0;
        totalWeight += weight;

        const record = { ...skill, weight, importance: isPref ? "preferred" : "required" };
        if (resumeSkills[name]) {
          matchedWeight += weight;
          matched.push(record);
        } else {
          if (isPref) missingPref.push(record);
          else missingReq.push(record);
        }
      });

      Object.keys(resumeSkills).forEach(name => {
        if (!jdSkills[name]) {
          additional.push(resumeSkills[name]);
        }
      });

      const skillMatchPct = totalWeight > 0 ? Math.round((matchedWeight / totalWeight) * 1000) / 10 : (matched.length > 0 ? 100 : 0);
      const cosSim = Math.round(clientCosineSimilarity(resumeText, finalJdText) * 1000) / 10;
      const composite = Math.round((skillMatchPct * 0.70 + cosSim * 0.30) * 10) / 10;

      // Category coverage
      const catBreakdown = {};
      Object.keys(CATEGORY_META).forEach(catKey => {
        const catTotal = Object.values(jdSkills).filter(s => s.category === catKey).length;
        const catMatch = matched.filter(s => s.category === catKey).length;
        const catCand = Object.values(resumeSkills).filter(s => s.category === catKey).length;
        
        let covPct = 0;
        if (catTotal > 0) {
          covPct = Math.round((catMatch / catTotal) * 100);
        } else if (catCand > 0) {
          covPct = 100;
        }

        catBreakdown[catKey] = {
          label: CATEGORY_META[catKey].label,
          color: CATEGORY_META[catKey].color,
          total_job_skills: catTotal,
          matched_skills: catMatch,
          missing_skills: Math.max(0, catTotal - catMatch),
          candidate_skills_count: catCand,
          candidate_skill_names: Object.values(resumeSkills).filter(s => s.category === catKey).map(s => s.name),
          coverage_pct: covPct
        };
      });

      // Topological Sort & Roadmap
      const allMissing = [...missingReq.map(s => s.name), ...missingPref.map(s => s.name)];
      const orderedSteps = [];
      let totalHours = 0;

      allMissing.forEach((skillName, idx) => {
        const res = SKILL_RESOURCES[skillName] || { hours: 15, diff: "Intermediate", doc: `https://www.google.com/search?q=${skillName}`, proj: `Build a project demonstrating ${skillName}.` };
        totalHours += res.hours;
        orderedSteps.push({
          step_number: idx + 1,
          skill_name: skillName,
          importance_label: missingReq.some(s => s.name === skillName) ? "High Priority (Required)" : "Secondary (Preferred)",
          difficulty: res.diff,
          est_hours: res.hours,
          prerequisites: PREREQUISITES_DAG[skillName] || [],
          syllabus: [`Foundations of ${skillName}`, `Production integration and testing`],
          mini_project: res.proj,
          resources: [{ title: `${skillName} Documentation`, url: res.doc, cost: "Free" }]
        });
      });

      const milestones = [];
      if (orderedSteps.length > 0) {
        milestones.push({
          phase: 1,
          title: "Phase 1: Core Required Competencies",
          description: "Close foundational gaps to qualify for the target position.",
          est_weeks: Math.max(1, Math.round(totalHours / 15)),
          steps: orderedSteps.slice(0, 3)
        });
        if (orderedSteps.length > 3) {
          milestones.push({
            phase: 2,
            title: "Phase 2: Advanced Specialization & Differentiators",
            description: "Master modern ecosystem tools and cloud integrations.",
            est_weeks: 2,
            steps: orderedSteps.slice(3)
          });
        }
        milestones.push({
          phase: milestones.length + 1,
          title: `Phase ${milestones.length + 1}: Comprehensive Capstone Project`,
          description: "Integrate newly acquired skills into a demonstrable public portfolio project.",
          est_weeks: 2,
          steps: [{
            step_number: orderedSteps.length + 1,
            skill_name: "Integrated Capstone Deliverable",
            importance_label: "Synthesis Milestone",
            difficulty: "Capstone",
            est_hours: 20,
            syllabus: ["Architect clean multi-tier repository", "Implement core domain logic with unit tests", "CI/CD automated deployment"],
            mini_project: `Construct an end-to-end demonstrable application showcasing ${allMissing.slice(0, 3).join(", ")}.`,
            resources: [{ title: "GitHub Portfolio Best Practices", url: "https://github.com/readme/guides/portfolio-readme", cost: "Free" }]
          }]
        });
      }

      let tier = "Job-Ready Candidate", badge = "Excellent Fit", color = "#10b981", desc = "Candidate demonstrates strong alignment with core requirements.";
      if (composite < 50) { tier = "Substantial Skill Gap"; badge = "Transition Needed"; color = "#ef4444"; desc = "Significant upskilling required across multiple foundational competencies."; }
      else if (composite < 70) { tier = "Moderate Gap (Targeted Upskilling)"; badge = "Upskilling Required"; color = "#f59e0b"; desc = "Solid foundation present; close key required qualification gaps."; }
      else if (composite < 85) { tier = "Strong Candidate (Minor Gaps)"; badge = "High Potential"; color = "#3b82f6"; desc = "Strong overlap with core competencies; minor secondary gaps."; }

      const jobRecommendations = clientFindMatchingJobs(resumeText);

      return {
        id: Date.now(),
        scores: {
          composite_readiness_score: composite,
          weighted_skill_match_pct: skillMatchPct,
          semantic_vector_sim_pct: cosSim,
          readiness_tier: tier,
          readiness_badge: badge,
          readiness_color: color,
          readiness_desc: desc
        },
        stats: {
          total_job_skills: Object.keys(jdSkills).length,
          matched_skills_count: matched.length,
          missing_required_count: missingReq.length,
          missing_preferred_count: missingPref.length,
          additional_skills_count: additional.length
        },
        skills: {
          matched,
          missing_required: missingReq,
          missing_preferred: missingPref,
          additional
        },
        category_breakdown: catBreakdown,
        job_recommendations: jobRecommendations,
        learning_path: {
          summary: { total_estimated_hours: totalHours + 20, estimated_completion_weeks: Math.max(2, Math.round((totalHours + 20) / 12)) },
          milestones
        },
        meta: { candidate_name: candidateName, job_title: jobTitle }
      };
    }

    // Controller Initialization
    document.addEventListener("DOMContentLoaded", async () => {
      const resumeTabs = document.querySelectorAll("#resumeTabs .tab-btn");
      const jdTabs = document.querySelectorAll("#jdTabs .tab-btn");
      const resumeUploadTab = document.getElementById("resumeUploadTab");
      const resumeTextTab = document.getElementById("resumeTextTab");
      const jdTextTab = document.getElementById("jdTextTab");
      const jdUrlTab = document.getElementById("jdUrlTab");

      const dropzone = document.getElementById("dropzone");
      const resumeFileInput = document.getElementById("resumeFileInput");
      const dropzoneContent = document.getElementById("dropzoneContent");
      const filePreview = document.getElementById("filePreview");
      const selectedFileName = document.getElementById("selectedFileName");
      const selectedFileSize = document.getElementById("selectedFileSize");
      const fileExtIcon = document.getElementById("fileExtIcon");
      const removeFileBtn = document.getElementById("removeFileBtn");

      const candidateNameInput = document.getElementById("candidateNameInput");
      const resumeTextInput = document.getElementById("resumeTextInput");
      const jobTitleInput = document.getElementById("jobTitleInput");
      const jdTextInput = document.getElementById("jdTextInput");
      const jdUrlInput = document.getElementById("jdUrlInput");
      const fetchUrlBtn = document.getElementById("fetchUrlBtn");
      const scrapedPreview = document.getElementById("scrapedPreview");

      const runAnalysisBtn = document.getElementById("runAnalysisBtn");
      const analysisSpinner = document.getElementById("analysisSpinner");
      const alertBanner = document.getElementById("alertBanner");
      const resultsDashboard = document.getElementById("resultsDashboard");
      const systemModeBadge = document.getElementById("systemModeBadge");

      const presetsContainer = document.getElementById("presetsContainer");
      const historyBtn = document.getElementById("historyBtn");
      const historyCount = document.getElementById("historyCount");
      const historyDrawer = document.getElementById("historyDrawer");
      const drawerBackdrop = document.getElementById("drawerBackdrop");
      const closeDrawerBtn = document.getElementById("closeDrawerBtn");
      const historyListContainer = document.getElementById("historyListContainer");

      let hasBackend = false;
      let selectedFile = null;
      let currentReport = null;
      let activeFilter = "all";

      // Detect Backend
      try {
        const res = await fetch("/health", { method: "GET" });
        if (res.ok) {
          hasBackend = true;
          systemModeBadge.textContent = "● FastAPI Server Active";
          systemModeBadge.style.color = "#34d399";
        }
      } catch (e) {
        hasBackend = false;
        systemModeBadge.textContent = "● Standalone Engine";
      }

      // Presets
      SAMPLE_PRESETS.forEach(p => {
        const btn = document.createElement("button");
        btn.className = "preset-chip";
        btn.textContent = p.label;
        btn.addEventListener("click", () => {
          candidateNameInput.value = p.candidate;
          jobTitleInput.value = p.job;
          resumeTextInput.value = p.resume;
          jdTextInput.value = p.jd;

          resumeTabs.forEach(b => b.classList.remove("active"));
          document.querySelector('#resumeTabs [data-tab="text"]').classList.add("active");
          resumeUploadTab.classList.remove("active");
          resumeTextTab.classList.add("active");

          jdTabs.forEach(b => b.classList.remove("active"));
          document.querySelector('#jdTabs [data-tab="jd-text"]').classList.add("active");
          jdUrlTab.classList.remove("active");
          jdTextTab.classList.add("active");

          showAlert(`Loaded preset: "${p.label}"`, "success");
        });
        presetsContainer.appendChild(btn);
      });

      // Tabs
      resumeTabs.forEach(btn => {
        btn.addEventListener("click", () => {
          resumeTabs.forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
          if (btn.getAttribute("data-tab") === "upload") {
            resumeUploadTab.classList.add("active");
            resumeTextTab.classList.remove("active");
          } else {
            resumeUploadTab.classList.remove("active");
            resumeTextTab.classList.add("active");
          }
        });
      });

      jdTabs.forEach(btn => {
        btn.addEventListener("click", () => {
          jdTabs.forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
          if (btn.getAttribute("data-tab") === "jd-text") {
            jdTextTab.classList.add("active");
            jdUrlTab.classList.remove("active");
          } else {
            jdTextTab.classList.remove("active");
            jdUrlTab.classList.add("active");
          }
        });
      });

      // File handling
      dropzone.addEventListener("click", (e) => {
        if (e.target !== removeFileBtn && !removeFileBtn.contains(e.target)) resumeFileInput.click();
      });

      dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("drag-over"); });
      dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-over"));
      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("drag-over");
        if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
      });

      resumeFileInput.addEventListener("change", () => {
        if (resumeFileInput.files.length > 0) handleFile(resumeFileInput.files[0]);
      });

      removeFileBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        selectedFile = null;
        resumeFileInput.value = "";
        filePreview.classList.add("hidden");
        dropzoneContent.classList.remove("hidden");
        if (fileExtractStatus) fileExtractStatus.classList.add("hidden");
      });

      const fileExtractStatus = document.getElementById("fileExtractStatus");
      const extractedWordCount = document.getElementById("extractedWordCount");
      const extractedTextSnippet = document.getElementById("extractedTextSnippet");
      const viewExtractedTextBtn = document.getElementById("viewExtractedTextBtn");

      if (viewExtractedTextBtn) {
        viewExtractedTextBtn.addEventListener("click", () => {
          resumeTabs.forEach(b => b.classList.remove("active"));
          const textTabBtn = document.querySelector('#resumeTabs .tab-btn[data-tab="text"]');
          if (textTabBtn) textTabBtn.classList.add("active");
          resumeUploadTab.classList.remove("active");
          resumeTextTab.classList.add("active");
          resumeTextInput.focus();
        });
      }

      async function handleFile(file) {
        selectedFile = file;
        selectedFileName.textContent = file.name;
        selectedFileSize.textContent = (file.size / 1024).toFixed(1) + " KB";
        const ext = file.name.split(".").pop().toLowerCase();
        fileExtIcon.textContent = ext.toUpperCase();
        dropzoneContent.classList.add("hidden");
        filePreview.classList.remove("hidden");

        if (fileExtractStatus) {
          fileExtractStatus.classList.remove("hidden");
          extractedWordCount.innerHTML = `<span class="mini-spinner"></span> Extracting text from ${file.name}...`;
          extractedTextSnippet.textContent = "Parsing document content...";
        }

        try {
          let extractedText = "";
          if (ext === "txt") {
            extractedText = await file.text();
          } else if (ext === "pdf") {
            extractedText = await parsePdfClient(file);
          } else if (ext === "docx") {
            extractedText = await parseDocxClient(file);
          }

          if (extractedText && extractedText.trim().length > 10) {
            resumeTextInput.value = extractedText;
            const words = extractedText.trim().split(/\s+/).length;
            if (extractedWordCount) {
              extractedWordCount.innerHTML = `✓ Successfully extracted <strong>${words.toLocaleString()} words</strong>`;
            }
            if (extractedTextSnippet) {
              extractedTextSnippet.textContent = extractedText.trim().slice(0, 280) + (extractedText.length > 280 ? "..." : "");
            }

            // Auto-detect candidate name from first non-empty lines
            const lines = extractedText.split("\n").map(l => l.trim()).filter(Boolean);
            if (lines.length > 0 && !candidateNameInput.value.includes("Alex") && !candidateNameInput.value.includes("Maya") && !candidateNameInput.value.includes("Jordan")) {
              const potential = lines[0].replace(/[^a-zA-Z\s.-]/g, "").trim();
              if (potential.length > 2 && potential.length < 35 && potential.split(" ").length <= 4) {
                candidateNameInput.value = potential;
              }
            }
          } else {
            if (extractedWordCount) {
              extractedWordCount.innerHTML = `✓ File ready (${file.name})`;
            }
            if (extractedTextSnippet) {
              extractedTextSnippet.textContent = "Document uploaded. Server-side deep parsing will be used during analysis.";
            }
          }
        } catch (err) {
          console.warn("Client file parsing error:", err);
          if (extractedWordCount) extractedWordCount.textContent = "Document attached";
          if (extractedTextSnippet) extractedTextSnippet.textContent = file.name;
        }
      }

      // Scraping URL
      fetchUrlBtn.addEventListener("click", async () => {
        const url = jdUrlInput.value.trim();
        if (!url) return showAlert("Please provide a valid URL.", "danger");

        if (hasBackend) {
          try {
            const res = await fetch(`${API_BASE}/api/scrape-jd`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ url })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail);
            scrapedPreview.value = data.text;
            scrapedPreview.classList.remove("hidden");
            if (data.title) jobTitleInput.value = data.title;
            showAlert("Job description fetched from URL!", "success");
          } catch (e) {
            showAlert(e.message, "danger");
          }
        } else {
          showAlert("URL scraping requires the backend server. Paste JD text directly or launch uvicorn.", "warning");
        }
      });

      // Main Analyze Action
      runAnalysisBtn.addEventListener("click", async () => {
        hideAlert();
        const candidateName = candidateNameInput.value.trim() || "Candidate Profile";
        const jobTitle = jobTitleInput.value.trim() || "Target Job Role";
        let resumeText = resumeTextInput.value.trim();
        let jdText = jdTextInput.value.trim() || scrapedPreview.value.trim();
        const isUpload = resumeUploadTab.classList.contains("active");

        if (!resumeText && !selectedFile) {
          return showAlert("Please upload a resume file (.pdf, .docx, .txt) or paste your resume content.", "danger");
        }

        // If no Job Description provided, automatically benchmark against standard role requirements
        if (!jdText || jdText.length < 20) {
          jdText = getClientBenchmarkJd(jobTitle, resumeText);
          jdTextInput.value = jdText;
        }

        runAnalysisBtn.disabled = true;
        analysisSpinner.classList.remove("hidden");

        try {
          let report;

          if (hasBackend) {
            if (selectedFile) {
              const formData = new FormData();
              formData.append("resume_file", selectedFile);
              if (resumeText) formData.append("resume_text", resumeText);
              formData.append("candidate_name", candidateName);
              formData.append("job_title", jobTitle);
              formData.append("jd_text", jdText);

              const res = await fetch(`${API_BASE}/api/analyze`, { method: "POST", body: formData });
              report = await res.json();
              if (!res.ok) throw new Error(report.detail || "Server error analyzing resume");
            } else {
              const res = await fetch(`${API_BASE}/api/analyze/direct`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ resume_text: resumeText, jd_text: jdText, candidate_name: candidateName, job_title: jobTitle })
              });
              report = await res.json();
              if (!res.ok) throw new Error(report.detail || "Server error analyzing resume");
            }
          } else {
            // Standalone Engine Execution (Works with any resume)
            report = runClientAnalysis(resumeText, jdText, candidateName, jobTitle);
            saveLocalHistory(report);
          }

          currentReport = report;
          renderResults(report);
          updateHistoryCount();
          showAlert("Analysis complete! Skill gaps, company matches & roadmap generated.", "success");
          resultsDashboard.scrollIntoView({ behavior: "smooth" });
        } catch (e) {
          showAlert(e.message, "danger");
        } finally {
          runAnalysisBtn.disabled = false;
          analysisSpinner.classList.add("hidden");
        }
      });

      // Render Results
      function renderResults(report) {
        resultsDashboard.classList.remove("hidden");
        const scores = report.scores;
        const stats = report.stats;

        const comp = Math.round(scores.composite_readiness_score);
        document.getElementById("compositeScoreText").textContent = `${comp}%`;
        const circle = document.getElementById("circleProgress");
        circle.setAttribute("stroke-dasharray", `${comp}, 100`);
        circle.style.stroke = scores.readiness_color;

        const badge = document.getElementById("readinessBadge");
        badge.textContent = scores.readiness_badge;
        badge.style.color = scores.readiness_color;
        badge.style.background = `${scores.readiness_color}22`;

        document.getElementById("readinessTierText").textContent = scores.readiness_tier;
        document.getElementById("readinessDescText").textContent = scores.readiness_desc;

        document.getElementById("weightedSkillScore").textContent = `${scores.weighted_skill_match_pct}%`;
        document.getElementById("skillScoreFill").style.width = `${scores.weighted_skill_match_pct}%`;

        document.getElementById("vectorSimScore").textContent = `${scores.semantic_vector_sim_pct}%`;
        document.getElementById("vectorScoreFill").style.width = `${scores.semantic_vector_sim_pct}%`;

        document.getElementById("statMatched").textContent = stats.matched_skills_count;
        document.getElementById("statMissingReq").textContent = stats.missing_required_count;
        document.getElementById("statMissingPref").textContent = stats.missing_preferred_count;
        document.getElementById("statAdditional").textContent = stats.additional_skills_count;

        document.getElementById("pillCountMatched").textContent = stats.matched_skills_count;
        document.getElementById("pillCountReq").textContent = stats.missing_required_count;
        document.getElementById("pillCountPref").textContent = stats.missing_preferred_count;
        document.getElementById("pillCountAdd").textContent = stats.additional_skills_count;

        // Categories
        const catContainer = document.getElementById("categoryBarsContainer");
        catContainer.innerHTML = "";
        let renderedCats = 0;
        Object.keys(report.category_breakdown || {}).forEach(k => {
          const cat = report.category_breakdown[k];
          const hasJobSkills = (cat.total_job_skills || 0) > 0;
          const hasCandSkills = (cat.candidate_skills_count || 0) > 0 || (cat.matched_skills || 0) > 0;

          if (!hasJobSkills && !hasCandSkills) return;
          renderedCats++;

          const div = document.createElement("div");
          div.className = "category-bar-item";

          let footerHtml = "";
          if (hasJobSkills) {
            footerHtml = `<span>${cat.matched_skills} of ${cat.total_job_skills} matched</span><span>${cat.missing_skills} missing</span>`;
          } else {
            const count = cat.candidate_skills_count || cat.matched_skills || 1;
            footerHtml = `<span>${count} candidate skill${count > 1 ? 's' : ''} verified</span><span>Profile Strength</span>`;
          }

          div.innerHTML = `
            <div class="cat-header">
              <span class="cat-title"><span class="cat-dot" style="background:${cat.color}"></span>${cat.label}</span>
              <span class="cat-pct" style="color:${cat.color}">${Math.round(cat.coverage_pct)}%</span>
            </div>
            <div class="cat-track"><div class="cat-fill" style="width:${cat.coverage_pct}%; background:${cat.color}"></div></div>
            <div class="cat-footer">${footerHtml}</div>
          `;
          catContainer.appendChild(div);
        });

        if (renderedCats === 0) {
          catContainer.innerHTML = `
            <div style="grid-column: 1 / -1; padding: 1.5rem; text-align: center; background: rgba(255,255,255,0.03); border: 1px dashed rgba(255,255,255,0.1); border-radius: 10px;">
              <p style="color: #94a3b8; margin: 0; font-size: 0.95rem;">No domain skills mapped yet. Add skills to your resume or job description to see category coverage.</p>
            </div>
          `;
        }

        // Skills Grid
        renderSkillsGrid(report.skills);

        // Resume-Matched Jobs & Direct Career Offers
        renderJobMatches(report.job_recommendations || (report.meta ? clientFindMatchingJobs(resumeTextInput.value) : null));

        // Roadmap
        renderRoadmap(report.learning_path);
      }

      function renderSkillsGrid(skills) {
        const container = document.getElementById("skillsGridContainer");
        container.innerHTML = "";
        const all = [];
        (skills.matched || []).forEach(s => all.push({ ...s, type: "matched", tag: "tag-matched", label: "Matched" }));
        (skills.missing_required || []).forEach(s => all.push({ ...s, type: "missing_req", tag: "tag-req", label: "Missing Required" }));
        (skills.missing_preferred || []).forEach(s => all.push({ ...s, type: "missing_pref", tag: "tag-pref", label: "Missing Preferred" }));
        (skills.additional || []).forEach(s => all.push({ ...s, type: "additional", tag: "tag-add", label: "Profile Bonus" }));

        const filtered = all.filter(s => activeFilter === "all" || s.type === activeFilter);
        
        if (filtered.length === 0) {
          let emptyMsg = "No skills in this category";
          let emptySub = "Try selecting 'All Skills' or adding more keywords to your resume/job description.";
          if (activeFilter === "matched") {
            emptyMsg = "No Direct Skill Matches";
            emptySub = "Job requirements have not matched candidate resume keywords yet.";
          } else if (activeFilter === "missing_req") {
            emptyMsg = "No Missing Required Skills";
            emptySub = "Candidate meets all essential qualifications for this target role!";
          } else if (activeFilter === "missing_pref") {
            emptyMsg = "No Missing Preferred Skills";
            emptySub = "Candidate satisfies or exceeds all nice-to-have qualifications.";
          } else if (activeFilter === "additional") {
            emptyMsg = "No Profile Bonus Skills";
            emptySub = "All candidate competencies match job requirements directly.";
          }

          container.innerHTML = `
            <div style="grid-column: 1 / -1; padding: 2.5rem 1.5rem; text-align: center; background: rgba(255,255,255,0.02); border: 1px dashed rgba(255,255,255,0.1); border-radius: 12px; margin: 0.5rem 0;">
              <div style="font-size: 1.75rem; margin-bottom: 0.5rem; opacity: 0.8;">📌</div>
              <h4 style="color: #f1f5f9; font-size: 1.05rem; font-weight: 600; margin: 0 0 0.25rem 0;">${emptyMsg}</h4>
              <p style="color: #94a3b8; font-size: 0.875rem; margin: 0;">${emptySub}</p>
            </div>
          `;
          return;
        }

        filtered.forEach(s => {
          const card = document.createElement("div");
          card.className = "skill-card";
          card.innerHTML = `
            <div class="skill-card-top">
              <span class="skill-name">${s.name}</span>
              <span class="skill-tag ${s.tag}">${s.label}</span>
            </div>
            <p class="skill-desc">${s.description || "Core engineering competency"}</p>
            <div class="skill-footer">
              <span>${s.category_label || s.category}</span>
              ${s.weight ? `<span>Weight: ${s.weight}x</span>` : ""}
            </div>
          `;
          container.appendChild(card);
        });
      }

      function renderJobMatches(jobData) {
        if (!jobData) return;
        const portals = jobData.global_portal_links || {};
        if (portals.linkedin) document.getElementById("portalLinkedIn").href = portals.linkedin;
        if (portals.google_jobs) document.getElementById("portalGoogle").href = portals.google_jobs;
        if (portals.indeed) document.getElementById("portalIndeed").href = portals.indeed;
        if (portals.wellfound) document.getElementById("portalWellfound").href = portals.wellfound;
        if (portals.remoteok) document.getElementById("portalRemoteOK").href = portals.remoteok;

        const container = document.getElementById("jobCardsContainer");
        container.innerHTML = "";
        const jobs = jobData.recommended_jobs || [];

        if (jobs.length === 0) {
          container.innerHTML = `<p class="field-hint">No specific company openings matched. Use the 1-Click live search portals above.</p>`;
          return;
        }

        jobs.forEach(job => {
          const card = document.createElement("div");
          card.className = "job-card";
          const matchedChips = (job.matched_skills || []).map(s => `<span class="job-skill-chip chip-matched">✓ ${s}</span>`).join("");
          const neededChips = (job.missing_skills || []).map(s => `<span class="job-skill-chip chip-needed">+ ${s}</span>`).join("");

          card.innerHTML = `
            <div>
              <div class="job-card-top">
                <div class="job-company-wrap">
                  <div class="job-company-logo" style="background:${job.company_color || '#6366f1'}">${job.company_logo || '★'}</div>
                  <div>
                    <span class="job-company-name">${job.company}</span>
                    <h4 class="job-title">${job.role_title}</h4>
                  </div>
                </div>
                <span class="job-match-badge">${Math.round(job.match_pct)}% Match</span>
              </div>

              <div class="job-meta-row" style="margin: 10px 0;">
                <span class="job-meta-item">📍 ${job.location}</span>
                ${job.salary_range ? `<span class="job-meta-item">💰 ${job.salary_range}</span>` : ""}
              </div>

              <p class="job-desc-snippet">${job.description || ""}</p>

              <div style="margin: 12px 0 6px;">
                <div style="font-size:11px; font-weight:700; color:var(--text-muted); margin-bottom:4px;">VERIFIED SKILLS OVERLAP:</div>
                <div class="job-skills-chips">
                  ${matchedChips}
                  ${neededChips}
                </div>
              </div>
            </div>

            <div class="job-actions-row">
              <a href="${job.direct_apply_url}" target="_blank" rel="noopener noreferrer" class="btn-apply-direct">
                Apply on Company Site
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              </a>
              <div class="job-portal-links-mini">
                ${job.portal_links?.linkedin ? `<a href="${job.portal_links.linkedin}" target="_blank" rel="noopener noreferrer" class="mini-portal-link">LinkedIn</a>` : ""}
                ${job.portal_links?.google_jobs ? `<a href="${job.portal_links.google_jobs}" target="_blank" rel="noopener noreferrer" class="mini-portal-link">Google</a>` : ""}
                ${job.portal_links?.indeed ? `<a href="${job.portal_links.indeed}" target="_blank" rel="noopener noreferrer" class="mini-portal-link">Indeed</a>` : ""}
              </div>
            </div>
          `;
          container.appendChild(card);
        });
      }

      // Filter pills
      document.querySelectorAll("#skillFilterPills .pill").forEach(p => {
        p.addEventListener("click", () => {
          document.querySelectorAll("#skillFilterPills .pill").forEach(x => x.classList.remove("active"));
          p.classList.add("active");
          activeFilter = p.getAttribute("data-filter");
          if (currentReport) renderSkillsGrid(currentReport.skills);
        });
      });

      function renderRoadmap(lp) {
        const container = document.getElementById("milestonesContainer");
        container.innerHTML = "";
        const summary = lp.summary || {};
        document.getElementById("roadmapTotalHours").textContent = `${summary.total_estimated_hours || 0} Hours`;
        document.getElementById("roadmapWeeks").textContent = `${summary.estimated_completion_weeks || 0} Weeks Plan`;

        (lp.milestones || []).forEach(m => {
          const block = document.createElement("div");
          block.className = "milestone-block";
          const stepsHtml = (m.steps || []).map(s => `
            <div class="step-card">
              <div class="step-top">
                <div class="step-title"><span class="step-num">${s.step_number}</span><span>${s.skill_name}</span></div>
                <div class="step-meta"><span>${s.importance_label}</span> • <strong>~${s.est_hours} hrs</strong></div>
              </div>
              ${s.prerequisites && s.prerequisites.length ? `<div style="font-size:11px;color:var(--text-dim);margin-bottom:6px">Prerequisites: <em>${s.prerequisites.join(", ")}</em></div>` : ""}
              ${s.mini_project ? `<div class="step-project-box"><strong>Hands-On Milestone:</strong> ${s.mini_project}</div>` : ""}
              <div class="step-resources">
                ${(s.resources || []).map(r => `<a href="${r.url}" target="_blank" class="resource-btn">${r.title} (${r.cost})</a>`).join("")}
              </div>
            </div>
          `).join("");

          block.innerHTML = `
            <div class="milestone-header">
              <div class="milestone-title-wrap"><h4>${m.title}</h4><p class="milestone-desc">${m.description}</p></div>
              <span class="milestone-badge">Est. ${m.est_weeks} Weeks</span>
            </div>
            <div class="step-cards-list">${stepsHtml}</div>
          `;
          container.appendChild(block);
        });
      }

      // History
      function saveLocalHistory(report) {
        const raw = localStorage.getItem("skillgap_history") || "[]";
        const list = JSON.parse(raw);
        list.unshift({
          id: report.id,
          date: new Date().toISOString(),
          candidate: report.meta.candidate_name,
          job: report.meta.job_title,
          score: report.scores.composite_readiness_score,
          matched: report.stats.matched_skills_count,
          missing: report.stats.missing_required_count,
          report: report
        });
        localStorage.setItem("skillgap_history", JSON.stringify(list.slice(0, 30)));
      }

      async function updateHistoryCount() {
        if (hasBackend) {
          try {
            const res = await fetch(`${API_BASE}/api/history`);
            const data = await res.json();
            historyCount.textContent = data.length;
            return;
          } catch(e) {}
        }
        const list = JSON.parse(localStorage.getItem("skillgap_history") || "[]");
        historyCount.textContent = list.length;
      }

      historyBtn.addEventListener("click", () => {
        historyDrawer.classList.remove("hidden");
        drawerBackdrop.classList.remove("hidden");
        loadHistory();
      });

      closeDrawerBtn.addEventListener("click", () => {
        historyDrawer.classList.add("hidden");
        drawerBackdrop.classList.add("hidden");
      });
      drawerBackdrop.addEventListener("click", () => {
        historyDrawer.classList.add("hidden");
        drawerBackdrop.classList.add("hidden");
      });

      async function loadHistory() {
        historyListContainer.innerHTML = "";
        let items = [];

        if (hasBackend) {
          try {
            const res = await fetch(`${API_BASE}/api/history`);
            items = await res.json();
          } catch(e) {}
        } else {
          items = JSON.parse(localStorage.getItem("skillgap_history") || "[]");
        }

        if (!items || items.length === 0) {
          historyListContainer.innerHTML = `<p class="field-hint">No evaluation runs recorded yet.</p>`;
          return;
        }

        items.forEach(it => {
          const div = document.createElement("div");
          div.className = "history-item";
          const title = it.candidate_name || it.candidate || "Candidate";
          const score = Math.round(it.composite_score !== undefined ? it.composite_score : it.score);
          const role = it.job_title || it.job || "Target Role";
          div.innerHTML = `
            <div class="history-item-top">
              <span class="history-title">${title}</span>
              <span class="history-score">${score}%</span>
            </div>
            <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px">Target: ${role}</div>
            <div class="history-meta"><span>${Math.round(score)}% Match</span></div>
          `;
          div.addEventListener("click", async () => {
            if (it.report) {
              currentReport = it.report;
              renderResults(it.report);
            } else if (hasBackend && it.id) {
              const res = await fetch(`/api/history/${it.id}`);
              const det = await res.json();
              if (det.report) {
                currentReport = det.report;
                renderResults(det.report);
              }
            }
            historyDrawer.classList.add("hidden");
            drawerBackdrop.classList.add("hidden");
            resultsDashboard.scrollIntoView({ behavior: "smooth" });
          });
          historyListContainer.appendChild(div);
        });
      }

      function showAlert(msg, type = "danger") {
        alertBanner.className = `alert-banner alert-${type}`;
        alertBanner.textContent = msg;
        alertBanner.classList.remove("hidden");
      }
      function hideAlert() { alertBanner.classList.add("hidden"); }

      updateHistoryCount();
    });