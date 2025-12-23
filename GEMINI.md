# Project Overview

This project implements a "Spec-Driven Development" workflow. It provides a set of shell scripts to structure and streamline the process of creating new features. The core idea is to define a feature's specification in detail before starting the implementation.

The workflow is managed through a series of commands, likely aliased as `/speckit.*`, which automate the creation of feature branches, specification files, and other related artifacts.

## Key Directories

*   `.specify/`: This directory contains the core of the workflow, including:
    *   `scripts/bash/`: The shell scripts that automate the development process.
    *   `templates/`: Templates for the various specification files.
    *   `memory/`: Likely used for storing context or state for the AI agent.
*   `specs/`: This directory contains the specifications for each feature. Each feature has its own subdirectory, named after the feature branch (e.g., `001-new-feature`), which contains files like:
    *   `spec.md`: The detailed specification of the feature.
    *   `plan.md`: The implementation plan.
    *   `tasks.md`: A checklist of tasks for the implementation.
    *   `research.md`: Research notes.
    *   `data-model.md`: Data model definitions.
    *   `quickstart.md`: A quickstart guide for the feature.
    *   `contracts/`: API contracts or other formal agreements.
*   `.claude/` & `.gemini/`: These directories contain configurations for the Claude and Gemini AI assistants, respectively. They likely define custom commands and settings for interacting with the project.

## Building and Running

This project is a collection of shell scripts, so there is no formal build process. The primary way to interact with the aproject is by using the provided scripts.

### Creating a New Feature

To start a new feature, use the `create-new-feature.sh` script:

```bash
.specify/scripts/bash/create-new-feature.sh "Description of the new feature"
```

This will:

1.  Create a new git branch with a name like `###-feature-name`.
2.  Create a corresponding directory in `specs/`.
3.  Create a `spec.md` file in the new feature directory, based on the template in `.specify/templates/spec-template.md`.

### Feature Development Workflow

After creating a new feature, the intended workflow is to use a series of commands to generate the necessary specification files. These commands are likely intended to be run in an environment where they are aliased to shorter names (e.g., `/speckit.specify`).

1.  `/speckit.specify`: Flesh out the `spec.md` file with the detailed specification of the feature.
2.  `/speckit.plan`: Create a `plan.md` file that outlines the implementation plan.
3.  `/speckit.tasks`: Generate a `tasks.md` file with a checklist of implementation tasks.
4.  Implement the feature, following the plan and tasks.

## Development Conventions

*   **Branching:** All new features should be developed in a feature branch with the naming convention `###-feature-name`, where `###` is a three-digit number.
*   **Specification First:** Before writing any code, a detailed specification for the feature should be created.
*   **Use the Scripts:** The provided scripts should be used to manage the feature development lifecycle.
