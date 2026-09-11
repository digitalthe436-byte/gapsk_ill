"""Personalized Learning Path Recommendation Engine.

Maps identified skill gaps into concrete educational resources, tutorials,
and project deliverables. Uses topological sorting on a prerequisite DAG
to sequence learning milestones logically.
"""

from collections import defaultdict, deque
from typing import Dict, List, Set, Any, Optional

# Prerequisite Relationships DAG: skill -> list of direct prerequisites that should be learned before it
PREREQUISITES_DAG: Dict[str, List[str]] = {
    # Frontend Path
    "TypeScript": ["JavaScript"],
    "React": ["JavaScript", "HTML5/CSS3"],
    "Next.js": ["React", "JavaScript", "TypeScript"],
    "Vue.js": ["JavaScript", "HTML5/CSS3"],
    "Angular": ["TypeScript", "JavaScript"],
    "Redux": ["React", "JavaScript"],
    "Tailwind CSS": ["HTML5/CSS3"],
    "WebSockets": ["JavaScript", "Node.js"],

    # Backend Path
    "Node.js": ["JavaScript"],
    "Express.js": ["Node.js", "JavaScript"],
    "NestJS": ["TypeScript", "Node.js"],
    "FastAPI": ["Python"],
    "Django": ["Python", "SQL"],
    "Flask": ["Python"],
    "Spring Boot": ["Java"],
    "GraphQL": ["REST APIs"],
    "gRPC": ["REST APIs"],

    # Cloud & DevOps Path
    "Docker": ["Linux", "Bash/Shell"],
    "Kubernetes": ["Docker", "Linux"],
    "CI/CD": ["Git", "Bash/Shell"],
    "GitHub Actions": ["Git", "CI/CD"],
    "Terraform": ["Linux", "AWS"],
    "Ansible": ["Linux", "Bash/Shell"],
    "Nginx": ["Linux"],

    # Data & AI Path
    "Pandas": ["Python"],
    "NumPy": ["Python"],
    "Scikit-learn": ["Python", "NumPy", "Pandas"],
    "Machine Learning": ["Python", "NumPy", "Pandas", "Scikit-learn"],
    "Deep Learning": ["Machine Learning", "Python", "NumPy"],
    "PyTorch": ["Deep Learning", "Python", "NumPy"],
    "TensorFlow": ["Deep Learning", "Python", "NumPy"],
    "Natural Language Processing (NLP)": ["Machine Learning", "Python"],
    "Large Language Models (LLMs)": ["Natural Language Processing (NLP)", "Python"],
    "Computer Vision": ["Deep Learning", "Python"],
    "Apache Spark": ["Python", "SQL", "Data Pipelines / ETL"],
    "Data Pipelines / ETL": ["SQL", "Python"],

    # Databases
    "PostgreSQL": ["SQL"],
    "MySQL": ["SQL"],
    "SQL Server": ["SQL"],
    "Oracle Database": ["SQL"],
    "DBMS": ["SQL"],
    "Redis": ["Linux"],
    "Elasticsearch": ["REST APIs", "Linux"],

    # Architecture & Practices
    "Microservices": ["REST APIs", "Docker", "System Design"],
    "Event-Driven Architecture": ["Microservices", "System Design"],
    "Test-Driven Development (TDD)": ["Unit Testing"],
    "Data Structures & Algorithms": ["Object-Oriented Programming (OOP)"],
    "Software Testing & QA": ["Unit Testing"],
    "Bootstrap": ["HTML5/CSS3"],
    "jQuery": ["JavaScript"],
    "UI/UX Design": ["HTML5/CSS3"],
    "ASP.NET": ["C#"],
    "Laravel": ["PHP"],
    "Data Analysis": ["Python", "SQL"],
    "Power BI": ["Excel"],
    "Tableau": ["SQL"],
}

# Curated High-Quality Learning Resources & Syllabus Catalog
SKILL_RESOURCE_CATALOG: Dict[str, Dict[str, Any]] = {
    "Python": {
        "difficulty": "Beginner to Intermediate",
        "est_hours": 25,
        "syllabus": ["Core Syntax & Data Structures", "OOP & Dunder Methods", "Generators, Decorators, Context Managers", "Asyncio & Typing"],
        "resources": [
            {"title": "Official Python 3 Documentation & Tutorial", "url": "https://docs.python.org/3/tutorial/", "type": "Documentation", "cost": "Free"},
            {"title": "Real Python Comprehensive Learning Tracks", "url": "https://realpython.com/", "type": "Interactive / Course", "cost": "Free/Freemium"},
            {"title": "Automate the Boring Stuff with Python", "url": "https://automatetheboringstuff.com/", "type": "Book / Hands-on", "cost": "Free"}
        ],
        "project": "Build an asynchronous CLI data processing and API querying utility with type annotations and unit tests."
    },
    "JavaScript": {
        "difficulty": "Beginner to Intermediate",
        "est_hours": 25,
        "syllabus": ["ES6+ Syntax", "Closures & Scopes", "Event Loop & Promises/Async-Await", "DOM & Web APIs"],
        "resources": [
            {"title": "MDN JavaScript Developer Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "type": "Documentation", "cost": "Free"},
            {"title": "The Modern JavaScript Tutorial (javascript.info)", "url": "https://javascript.info/", "type": "Tutorial", "cost": "Free"}
        ],
        "project": "Develop an interactive event-driven state manager and real-time dashboard without frameworks."
    },
    "TypeScript": {
        "difficulty": "Intermediate",
        "est_hours": 15,
        "syllabus": ["Primitive & Compound Types", "Generics & Utility Types", "Interfaces vs Type Aliases", "Strict Compiler Settings"],
        "resources": [
            {"title": "TypeScript Official Handbook", "url": "https://www.typescriptlang.org/docs/handbook/intro.html", "type": "Documentation", "cost": "Free"},
            {"title": "Total TypeScript Tutorials by Matt Pocock", "url": "https://www.totaltypescript.com/tutorials", "type": "Interactive Course", "cost": "Free"}
        ],
        "project": "Refactor a vanilla JS codebase to TypeScript with strict type checking and custom generic utility types."
    },
    "React": {
        "difficulty": "Intermediate",
        "est_hours": 30,
        "syllabus": ["Component Lifecycle & Hooks", "State Management & Context", "Custom Hooks & Performance Memoization", "Server vs Client Components"],
        "resources": [
            {"title": "Official React Docs (react.dev)", "url": "https://react.dev/learn", "type": "Documentation / Interactive", "cost": "Free"},
            {"title": "Epic React by Kent C. Dodds", "url": "https://epicreact.dev/", "type": "Deep Dive Guide", "cost": "Freemium"}
        ],
        "project": "Architect a responsive multi-page dashboard application with custom hooks, caching, and optimistic UI updates."
    },
    "Next.js": {
        "difficulty": "Intermediate to Advanced",
        "est_hours": 20,
        "syllabus": ["App Router Architecture", "Server Actions & SSR/SSG/ISR", "Route Handlers & Middleware", "SEO & Core Web Vitals Optimization"],
        "resources": [
            {"title": "Next.js Official Documentation & Learn Course", "url": "https://nextjs.org/learn", "type": "Interactive Course", "cost": "Free"},
            {"title": "Vercel Next.js Templates & Best Practices", "url": "https://github.com/vercel/next.js/tree/canary/examples", "type": "Codebase Reference", "cost": "Free"}
        ],
        "project": "Deploy a full-stack SaaS portal utilizing App Router, Server Components, authentication, and Postgres integration."
    },
    "FastAPI": {
        "difficulty": "Intermediate",
        "est_hours": 18,
        "syllabus": ["Pydantic Data Models & Validation", "Dependency Injection System", "OAuth2 & JWT Authentication", "Async Endpoints & Background Tasks"],
        "resources": [
            {"title": "FastAPI Official Tutorial & User Guide", "url": "https://fastapi.tiangolo.com/tutorial/", "type": "Documentation", "cost": "Free"},
            {"title": "TestDriven.io FastAPI Microservices Guide", "url": "https://testdriven.io/guides/fastapi-crud/", "type": "Tutorial", "cost": "Free"}
        ],
        "project": "Build a production-ready asynchronous RESTful microservice with JWT auth, rate limiting, and OpenAPI docs."
    },
    "Docker": {
        "difficulty": "Intermediate",
        "est_hours": 15,
        "syllabus": ["Dockerfiles & Multi-Stage Builds", "Images, Layers & Caching", "Docker Compose Orchestration", "Volume Mounts & Networking"],
        "resources": [
            {"title": "Docker Official Getting Started Guide", "url": "https://docs.docker.com/get-started/", "type": "Documentation", "cost": "Free"},
            {"title": "Play with Docker Interactive Labs", "url": "https://labs.play-with-docker.com/", "type": "Hands-on Sandbox", "cost": "Free"}
        ],
        "project": "Containerize a multi-tier web application (FastAPI + PostgreSQL + Redis) using optimized multi-stage Dockerfiles."
    },
    "Kubernetes": {
        "difficulty": "Advanced",
        "est_hours": 35,
        "syllabus": ["Pods, Deployments, & ReplicaSets", "Services & Ingress Controllers", "ConfigMaps, Secrets, & Storage", "Helm Charts & Horizontal Pod Autoscaling"],
        "resources": [
            {"title": "Kubernetes Official Tutorials (k8s.io)", "url": "https://kubernetes.io/docs/tutorials/", "type": "Documentation", "cost": "Free"},
            {"title": "KubeAcademy by VMware", "url": "https://kube.academy/", "type": "Video Course", "cost": "Free"}
        ],
        "project": "Deploy an autoscaling microservices cluster on Minikube or cloud k8s with zero-downtime rolling updates."
    },
    "AWS": {
        "difficulty": "Intermediate to Advanced",
        "est_hours": 30,
        "syllabus": ["Compute (EC2, Lambda, ECS)", "Storage & DB (S3, RDS, DynamoDB)", "Networking (VPC, Route53, CloudFront)", "IAM Security Policies"],
        "resources": [
            {"title": "AWS Skill Builder Official Digital Courses", "url": "https://explore.skillbuilder.aws/", "type": "Official Training", "cost": "Free"},
            {"title": "AWS Free Tier Hands-On Projects", "url": "https://aws.amazon.com/getting-started/hands-on-tutorials/", "type": "Hands-on Lab", "cost": "Free"}
        ],
        "project": "Deploy a serverless backend with API Gateway, AWS Lambda, DynamoDB, and automated S3 static hosting."
    },
    "PostgreSQL": {
        "difficulty": "Intermediate",
        "est_hours": 20,
        "syllabus": ["Complex Joins & Aggregations", "Indexes (B-tree, GIN) & Query Plans", "ACID Transactions & Isolation Levels", "JSONB Document Storage"],
        "resources": [
            {"title": "PostgreSQL Official Documentation", "url": "https://www.postgresql.org/docs/", "type": "Documentation", "cost": "Free"},
            {"title": "Use The Index, Luke (SQL Indexing Guide)", "url": "https://use-the-index-luke.com/", "type": "Specialized Guide", "cost": "Free"}
        ],
        "project": "Design and benchmark a normalized relational database schema with indexed queries handling 100k+ rows."
    },
    "CI/CD": {
        "difficulty": "Intermediate",
        "est_hours": 14,
        "syllabus": ["Continuous Integration Pipelines", "Automated Linting & Test Runners", "Artifact Building & Semantic Versioning", "Deployment Automation"],
        "resources": [
            {"title": "GitHub Actions Documentation", "url": "https://docs.github.com/en/actions", "type": "Documentation", "cost": "Free"},
            {"title": "GitLab CI/CD Quick Start", "url": "https://docs.gitlab.com/ee/ci/quick_start/", "type": "Guide", "cost": "Free"}
        ],
        "project": "Configure a complete GitHub Actions CI/CD pipeline that tests, builds Docker images, and deploys on git push."
    },
    "Machine Learning": {
        "difficulty": "Intermediate to Advanced",
        "est_hours": 40,
        "syllabus": ["Supervised vs Unsupervised Learning", "Feature Engineering & Cross-Validation", "Regression, Classification, & Trees", "Model Evaluation & Hyperparameter Tuning"],
        "resources": [
            {"title": "Andrew Ng Machine Learning Specialization (DeepLearning.AI)", "url": "https://www.coursera.org/specializations/machine-learning-introduction", "type": "Course", "cost": "Freemium"},
            {"title": "Scikit-Learn Machine Learning Tutorials", "url": "https://scikit-learn.org/stable/tutorial/index.html", "type": "Documentation", "cost": "Free"}
        ],
        "project": "Train, evaluate, and tune an ensemble machine learning model predicting real estate prices or customer churn."
    },
    "PyTorch": {
        "difficulty": "Advanced",
        "est_hours": 35,
        "syllabus": ["Tensors & Autograd", "Building Neural Networks with nn.Module", "Custom Datasets & DataLoaders", "Training Loops & GPU Acceleration"],
        "resources": [
            {"title": "PyTorch Official 60-Minute Blitz & Tutorials", "url": "https://pytorch.org/tutorials/", "type": "Tutorials", "cost": "Free"},
            {"title": "Fast.ai Practical Deep Learning for Coders", "url": "https://course.fast.ai/", "type": "Course", "cost": "Free"}
        ],
        "project": "Train a custom CNN or Transformer model for image or text classification with PyTorch on GPU."
    },
    "REST APIs": {
        "difficulty": "Intermediate",
        "est_hours": 12,
        "syllabus": ["HTTP Methods, Headers & Status Codes", "RESTful Resource Modeling", "Idempotency & Error Payloads", "API Versioning & OpenAPI Specs"],
        "resources": [
            {"title": "RESTful API Architectural Constraints Guide", "url": "https://restfulapi.net/", "type": "Guide", "cost": "Free"},
            {"title": "OpenAPI / Swagger Specification Standard", "url": "https://swagger.io/specification/", "type": "Standard", "cost": "Free"}
        ],
        "project": "Design a clean RESTful resource API conforming strictly to RFC 7231 standards with Swagger documentation."
    },
    "System Design": {
        "difficulty": "Advanced",
        "est_hours": 30,
        "syllabus": ["Horizontal vs Vertical Scaling", "Load Balancing & Caching Strategies", "Database Sharding & Replication", "CAP Theorem & Fault Tolerance"],
        "resources": [
            {"title": "The System Design Primer (Donne Martin)", "url": "https://github.com/donnemartin/system-design-primer", "type": "Open Source Guide", "cost": "Free"},
            {"title": "High Scalability Real-World Architecture Case Studies", "url": "http://highscalability.com/", "type": "Case Studies", "cost": "Free"}
        ],
        "project": "Author a comprehensive RFC/Design Doc for a URL shortener or distributed chat system supporting 10k QPS."
    },
    "Linux": {
        "difficulty": "Beginner to Intermediate",
        "est_hours": 15,
        "syllabus": ["File System Hierarchy & Permissions", "Process Management & Systemd", "Networking Diagnostics (curl, netstat, ssh)", "Shell Automation"],
        "resources": [
            {"title": "Linux Journey Interactive Guide", "url": "https://linuxjourney.com/", "type": "Interactive Guide", "cost": "Free"},
            {"title": "The Linux Command Line (William Shotts)", "url": "https://linuxcommand.org/tlcl.php", "type": "Free Book", "cost": "Free"}
        ],
        "project": "Set up a hardened Linux VPS with SSH keys, fail2ban, firewall, and systemd service monitoring."
    }
}


def topological_sort_skills(skills: List[str], known_skills: Set[str]) -> List[str]:
    """Topologically sort missing skills based on the prerequisite DAG.

    Ensures that any prerequisites among the missing skills appear before
    the dependent skills. Skills without dependencies or with satisfied
    dependencies come first.
    """
    skill_set = set(skills)
    in_degree = {s: 0 for s in skill_set}
    graph = defaultdict(list)

    # Build dependency graph restricted to the missing skills
    for s in skill_set:
        prereqs = PREREQUISITES_DAG.get(s, [])
        for p in prereqs:
            if p in skill_set:
                # p must be learned before s
                graph[p].append(s)
                in_degree[s] += 1

    # Standard Kahn's algorithm for topological sorting
    queue = deque([s for s in skill_set if in_degree[s] == 0])
    ordered = []

    while queue:
        node = queue.popleft()
        ordered.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # If cycles or unvisited nodes exist, append them safely
    remaining = [s for s in skill_set if s not in ordered]
    ordered.extend(remaining)

    return ordered


def generate_learning_path(
    missing_required: List[Dict[str, Any]],
    missing_preferred: List[Dict[str, Any]],
    matched_skills: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate structured, step-by-step personalized learning path.

    Sequences milestones logically:
      Phase 1: Critical Foundational Gaps (Required prerequisites)
      Phase 2: Core Required Toolset & Frameworks
      Phase 3: Preferred & High-Leverage Differentiators
      Phase 4: Synthesis & Capstone Portfolio Project
    """
    known_skill_names = {s["name"] for s in matched_skills}

    req_names = [s["name"] for s in missing_required]
    pref_names = [s["name"] for s in missing_preferred]

    # Topologically sort required skills first
    ordered_req = topological_sort_skills(req_names, known_skill_names)
    ordered_pref = topological_sort_skills(pref_names, known_skill_names.union(set(req_names)))

    # Total estimated study time
    total_hours = 0
    all_ordered_names = ordered_req + ordered_pref

    enriched_steps = []
    for step_num, skill_name in enumerate(all_ordered_names, start=1):
        catalog_entry = SKILL_RESOURCE_CATALOG.get(skill_name, {
            "difficulty": "Intermediate",
            "est_hours": 15,
            "syllabus": [f"Core concepts of {skill_name}", f"Hands-on application and integration of {skill_name}"],
            "resources": [
                {"title": f"Official {skill_name} Documentation", "url": f"https://www.google.com/search?q={skill_name}+documentation", "type": "Documentation", "cost": "Free"},
                {"title": f"FreeCodeCamp Guide: {skill_name}", "url": f"https://www.freecodecamp.org/news/search/?query={skill_name}", "type": "Guide", "cost": "Free"}
            ],
            "project": f"Build a prototype application demonstrating practical mastery of {skill_name}."
        })

        is_required = skill_name in req_names
        hours = catalog_entry["est_hours"]
        total_hours += hours

        enriched_steps.append({
            "step_number": step_num,
            "skill_name": skill_name,
            "importance": "required" if is_required else "preferred",
            "importance_label": "High Priority (Required)" if is_required else "Secondary (Preferred)",
            "difficulty": catalog_entry["difficulty"],
            "est_hours": hours,
            "prerequisites": [p for p in PREREQUISITES_DAG.get(skill_name, []) if p in (set(all_ordered_names) | known_skill_names)],
            "syllabus": catalog_entry["syllabus"],
            "resources": catalog_entry["resources"],
            "mini_project": catalog_entry["project"]
        })

    # Divide steps into 3 to 4 sequential curriculum milestones
    milestones = []
    if enriched_steps:
        # Milestone 1: Foundations & High Priority Prerequisites
        m1_steps = [s for s in enriched_steps if s["importance"] == "required"][:3]
        if m1_steps:
            milestones.append({
                "phase": 1,
                "title": "Phase 1: Foundational & Core Required Competencies",
                "description": "Close the most impactful required job qualifications first to establish eligibility.",
                "steps": m1_steps,
                "est_weeks": max(1, round(sum(s["est_hours"] for s in m1_steps) / 10))
            })

        # Milestone 2: Remaining Required Skills
        m2_steps = [s for s in enriched_steps if s["importance"] == "required"][3:]
        if m2_steps:
            milestones.append({
                "phase": 2,
                "title": "Phase 2: Deep Technical Specialization",
                "description": "Master advanced frameworks and system tools mandated for the target role.",
                "steps": m2_steps,
                "est_weeks": max(1, round(sum(s["est_hours"] for s in m2_steps) / 10))
            })

        # Milestone 3: Preferred & Differentiator Skills
        m3_steps = [s for s in enriched_steps if s["importance"] == "preferred"]
        if m3_steps:
            milestones.append({
                "phase": 3 if len(milestones) == 2 else 2,
                "title": "Phase 3: Competitive Differentiators (Nice-to-Haves)",
                "description": "Elevate candidate standing by acquiring preferred secondary competencies.",
                "steps": m3_steps,
                "est_weeks": max(1, round(sum(s["est_hours"] for s in m3_steps) / 10))
            })

        # Phase 4: Capstone Project Integrating All Gaps
        milestones.append({
            "phase": len(milestones) + 1,
            "title": "Phase 4: Comprehensive Capstone Project & Portfolio",
            "description": "Integrate newly acquired skills into an end-to-end demonstrable public portfolio project.",
            "steps": [{
                "step_number": len(enriched_steps) + 1,
                "skill_name": "Integrated Capstone Deliverable",
                "importance": "required",
                "importance_label": "Synthesis Milestone",
                "difficulty": "Capstone",
                "est_hours": 20,
                "prerequisites": [s["skill_name"] for s in enriched_steps[:4]],
                "syllabus": [
                    "Repository Architecture & Clean Code Setup",
                    "Implementation of Core Business Logic",
                    "Automated Testing & CI/CD Pipeline",
                    "Cloud Deployment & Live Demo Link in Resume"
                ],
                "resources": [
                    {"title": "GitHub Portfolio Best Practices Guide", "url": "https://github.com/readme/guides/portfolio-readme", "type": "Guide", "cost": "Free"}
                ],
                "mini_project": f"Construct an end-to-end fullstack or data project integrating {', '.join([s['skill_name'] for s in enriched_steps[:3]])} with clean documentation and test coverage."
            }],
            "est_weeks": 2
        })

    return {
        "summary": {
            "total_missing_skills": len(all_ordered_names),
            "required_count": len(ordered_req),
            "preferred_count": len(ordered_pref),
            "total_estimated_hours": total_hours + 20,  # includes capstone
            "estimated_completion_weeks": max(2, round((total_hours + 20) / 12))  # assuming ~12 hrs/week
        },
        "milestones": milestones,
        "ordered_steps": enriched_steps
    }
