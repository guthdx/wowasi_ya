# **WOWASI_YA_MODEL_B_INTEGRATION.md**  
*Integration guide for Model B prompt library and Model A → Model B handoff schema*

---

## **1. Overview**

This document describes how to integrate two key components of the wowasi_ya system:

1. **Model B Prompt Library** (`prompts_model_b.yaml`)  
   A reusable set of document-generation prompts used by Model B (Llama 3.3 70B or equivalent) to produce polished project documents.

2. **Model A → Model B Handoff Schema** (`modelA_to_modelB_schema.json`)  
   A structured format defining what data Model A must output so Model B can generate documents consistently.

These components work together to produce a 15-document project planning packet with consistent tone, structure, and logic.

This file explains:

- Where to store these files  
- How they fit into the wowasi_ya folder structure  
- How Model A and Model B are expected to interact  
- How prompts are loaded and used during document generation  

This is the canonical integration guide for developers and automated agents working on this project.

---

## **2. Repository Location and Folder Structure**

The local path to this project is:

```
/Users/guthdx/terminal_projects/claude_code/wowasi_ya
```

Inside this project, the recommended structure for configuration files is:

```
wowasi_ya/
   config/
      prompts/
         prompts_model_b.yaml
      schemas/
         modelA_to_modelB_schema.json
```

This structure ensures modular, predictable configuration management.

---

## **3. Purpose of Each File**

### **3.1 prompts_model_b.yaml**

This file contains:

- The **system prompt** used by Model B  
- Fifteen **document-specific prompt templates**  
- Requirements for tone, structure, and content boundaries  
- Placeholder fields to be filled with structured data from Model A  

Model B uses this file to generate all planning documents, such as:

- Project Brief  
- Business Case  
- Scope & Boundaries  
- Risk Summary  
- Implementation Plan  
- Budget Outline  
- Data Governance Framework  
- And others  

This file must remain stable so Model B can reliably generate consistent outputs.

---

### **3.2 modelA_to_modelB_schema.json**

This file defines the exact JSON structure Model A must output.

It includes fields for:

- Core project frame  
- Concept map  
- Goals, risks, scope, stakeholders  
- Timeline model  
- Budget model  
- Document outline  
- Document type (`doc_type`)  

Model A produces a JSON object matching this schema.

Model B receives that JSON and uses it to fill placeholders in the templates from `prompts_model_b.yaml`.

This supports deterministic, repeatable document generation.

---

## **4. Model A → Model B Workflow**

The wowasi_ya document-generation workflow follows this sequence:

```
User → Model A → JSON output (structured planning data)
           |
           v
Load prompts_model_b.yaml → select correct template using doc_type
           |
           v
Merge JSON fields into YAML prompt
           |
           v
Send composed prompt to Model B (Llama 3.3 70B)
           |
           v
Model B returns the final document
```

### **Summary**
- Model A generates **content structure**  
- Model B generates **professional writing**  
- YAML defines **how** Model B writes  
- JSON defines **what** Model B writes about  

---

## **5. Where (and How) To Save the Files**

To create the correct directory structure:

```bash
cd /Users/guthdx/terminal_projects/claude_code/wowasi_ya

mkdir -p config/prompts
mkdir -p config/schemas
```

Then save:

```
config/prompts/prompts_model_b.yaml  
config/schemas/modelA_to_modelB_schema.json
```

Commit these to GitHub:

```bash
git add config/prompts/prompts_model_b.yaml
git add config/schemas/modelA_to_modelB_schema.json

git commit -m "Add Model B prompt library and Model A→B handoff schema"
git push
```

---

## **6. How Model B Uses prompts_model_b.yaml**

During document generation:

1. Load the YAML file.  
2. Read the `"system_prompt"`.  
3. Select the correct document template from `documents[doc_type]`.  
4. Replace all placeholders:
   - `{{PROJECT_FRAME}}`  
   - `{{CONCEPT_MAP}}`  
   - `{{PLANNING_DATA}}`  
   - `{{DOC_OUTLINE}}`  
   - `{{PREVIOUS_DOCS_SUMMARY}}`  
5. Send the composed prompt + system prompt to Model B.  
6. Model B returns the completed Markdown document.

Model B does not decide the structure; it only fills in templates.

---

## **7. How Model A Uses modelA_to_modelB_schema.json**

Model A’s job is to provide structured planning content.

Model A must output JSON matching the schema:

- Goals  
- Scope  
- Risks  
- Stakeholders  
- Timeline  
- Budget categories  
- Document outline  
- Document type  
- Optional summary of previously created documents  

Model B assumes the JSON is valid and does no internal validation.

A correct schema ensures consistency and prevents drift across documents.

---

## **8. Summary for Development AIs**

Any development agent must understand:

1. `prompts_model_b.yaml` is the **Model B writing engine**.  
2. `modelA_to_modelB_schema.json` defines **Model A’s required output format**.  
3. All wowasi_ya documents are generated via:
   - Structured JSON  
   - Template-based writing  
4. The folder structure under `config/` is canonical.  
5. No AI should move, rename, or restructure these files without updating this document.  

---

## **9. Recommended Future Additions (Optional)**

- A script to automatically merge Model A JSON with Model B templates  
- A JSON validator for Model A output  
- A CLI (`wowasi generate`)  
- GitHub Actions for automated document generation  
- n8n workflows for fully automated pipelines  

These improvements are optional and can be added over time.

---

# **End of File**
