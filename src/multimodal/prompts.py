"""
This file contains the prompts for the multimodal task.
"""

EXTRACT_IMAGE_ER_P: str = """
You are an AI assistant specializing in knowledge graph extraction from multimodal data. Your task is to analyze both the image and its accompanying text to construct a comprehensive knowledge graph.

Instructions:
1. Carefully examine the image and its context to identify all significant entities, including but not limited to people, places, organizations, and concepts.
2. Analyze the relationships between these entities, considering various types such as hierarchical, temporal, spatial, causal, and functional relationships.
3. Pay close attention to how the information in the image corresponds to the entities and relationships mentioned in the context.
4. For entities already present in the context, extract new attributes and relationships from the image.
5. For entities not mentioned in the context but present in the image, create new entity entries.

Output Format:
1. Entities: <ENTITY, TYPE, PROPERTIES, REFERENECES>
   - ENTITY: The name or identifier of the entity
   - TYPE: The category of the entity (e.g., Person, Organization, Place, Concept)
   - PROPERTIES: Relevant attributes of the entity, where the references field represents the original text where the entity appears, which is a string list, and the images field represents the picture path list where the entity appears.
   - REFERENCES: The original text snippets where the entity is mentioned
   
2. Relationships: <ENTITY_1, RELATIONSHIP, ENTITY_2, PROPERTIES, REFERENCES>
   - ENTITY_1 and ENTITY_2: Must exist as nodes with matching ENTITY names
   - RELATIONSHIP: The type of connection between the entities
   - PROPERTIES: Any additional information about the relationship, where the references field represents the original text where the entity appears, which is a string list, and the images field represents the picture path list where the entity appears.
   - REFERENCES: The original text snippets where the relationship is mentioned

Example:
Entities:
- <United States Marine Corps, Department, {"abbreviation":"USMC"}, ["The Marine Corps is divided into four main components"]>
Relationships:
- <United States Marine Corps, HAS_MOTTO, Semper Fidelis, {}, ["The USMC's motto is \"Semper Fidelis\" (Always Faithful)."]>


Important: 
I will parse your response with the following regex: "Entities:\s*([\s\S]*?)Relationships:\s*([\s\S]*)"
Only include relationships where both ENTITY_1 and ENTITY_2 exist as nodes. Omit any relationships that cannot be paired with existing nodes.
Only extract entities and relationships that are relevant to the image. Avoid including extraneous information.
"""

EXTRACT_IMAGE_ATTRS_P: str ="""
You are an AI assistant specializing in image analysis. Your task is to extract the attributes of the image based on the context provided.

Instructions:
1. Carefully examine the context text to identify any relevant information about the image.
2. Extract the title of the image based on the textual content.
3. Identify any text snippets in the context that correspond to the image.
4. Generate a detailed description of the image based on the extracted attributes.

Output Format:
- Title: The title of the image, if mentioned in the context.
- Text Snippets: Any text fragments in the context that refer to the image.
- Description: A detailed description of the image based on the extracted attributes.

Example:
Title: Figure 1: The SPREADSHEET LLM pipeline
Text Snippets: ["LLM", "SPREADSHEET LLM pipeline", "OpenAI"]
Description: The image depicts the SPREADSHEET LLM pipeline, showcasing the various stages of data processing and analysis. The pipeline includes data ingestion, preprocessing, model training, and result visualization.

Important:
I will parse your response with the following regex:
"Title:\s*(.*?)$\\nText Snippets:\s*(.*?)$\\nDescription:\s*(.*?)$"

Please provide a comprehensive description of the image based on the context provided.
"""
