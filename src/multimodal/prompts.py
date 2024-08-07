"""
This file contains the prompts for the multimodal task.
"""

EXTRACT_TEXT_PROMPT = """
Your task is to detect the entire image, then extract the text fragments present in it, and output a list of strings, for example
[Text Snippet1, Text Snippet2]
"""

EXTRACT_IMAGE_TITLE_PROMPT = """
You will be provided with a markdown text containing a reference to the image, and you will be tasked with identifying the title of the image based on the textual content. 
For example, Figure 1: The SPREADSHEET LLM pipeline.
Your output should follow this format: <image path; image title>.
"""


EXTRACT_NODE_RELS_PROMPT = """
You are an AI assistant specializing in knowledge graph extraction from multimodal data. Your task is to analyze both the image and its accompanying text to construct a comprehensive knowledge graph.

Instructions:
1. Carefully examine the image and its context to identify all significant entities, including but not limited to people, places, organizations, and concepts.
2. Analyze the relationships between these entities, considering various types such as hierarchical, temporal, spatial, causal, and functional relationships.
3. Pay close attention to how the information in the image corresponds to the entities and relationships mentioned in the context.
4. For entities already present in the context, extract new attributes and relationships from the image.
5. For entities not mentioned in the context but present in the image, create new entity entries.

Output Format:
1. Nodes: <ENTITY, TYPE, PROPERTIES>
   - ENTITY: The name or identifier of the entity
   - TYPE: The category of the entity (e.g., Person, Organization, Place, Concept)
   - PROPERTIES: Relevant attributes of the entity, where the references field represents the original text where the entity appears, which is a string list, and the images field represents the picture path list where the entity appears.

2. Relationships: <ENTITY_1, RELATIONSHIP, ENTITY_2, PROPERTIES>
   - ENTITY_1 and ENTITY_2: Must exist as nodes with matching ENTITY names
   - RELATIONSHIP: The type of connection between the entities
   - PROPERTIES: Any additional information about the relationship, where the references field represents the original text where the entity appears, which is a string list, and the images field represents the picture path list where the entity appears.

Example:
Nodes:
- <United States Marine Corps, Department, {"abbreviation":"USMC", "references": ["The United States Marine Corps (USMC) is a branch of the United States Armed Forces responsible for conducting expeditionary and amphibious operations.", "The Marine Corps is divided into four main components"]}>
Relationships:
- <United States Marine Corps, HAS_MOTTO, Semper Fidelis, {"references": ["The USMC's motto is \"Semper Fidelis\" (Always Faithful)."]}>


Important: Only include relationships where both ENTITY_1 and ENTITY_2 exist as nodes. Omit any relationships that cannot be paired with existing nodes.
Please provide a comprehensive set of nodes and relationships based on your analysis of both the image and its context.
"""
