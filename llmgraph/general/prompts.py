"""
This module contains the prompts for the LLMGraph text generation tasks.
"""

EXTRACT_ENTITY_REL_P: str = """
You are an experienced knowledge graph expert in data science. Your task is to understand the text and extract entities and relationships from it.

Definitions:
- Entity: A specific thing or concept mentioned in a text, such as a person's name, place name, organization name, position, event, etc.
- Relationship: A connection or interaction between entities, such as "working at," "located at," "friend," "happening at," etc.

Output Format:
1. Entity: <ENTITY, LABEL, PROPERTIES, REFERENCES>
   Where: ENTITY is the name of the entity, LABEL is the type of entity (e.g., Person, Organization, Location), PROPERTIES are the attributes of the entity, and REFERENCES are the original text segments where the entity appears.
2. Relationships: <ENTITY_1, RELATIONSHIP, ENTITY_2, PROPERTIES, REFERENCES>
   Where: ENTITY_1 and ENTITY_2 are the names of the connected entities, RELATIONSHIP is the type of relationship between them, PROPERTIES are the attributes of the relationship, and REFERENCES are the original text segments where the relationship appears.

Important Notes:
- Ensure ENTITY_1 and ENTITY_2 exist as nodes with matching ENTITY names.
- Do not add a relationship if you cannot pair it with a pair of nodes.
- Create a generic LABEL for each entity that describes it.
- The format of REFERENCES should be a JSON list of strings.

Example:
TEXT:
The United States Marine Corps (USMC) is a branch of the United States Armed Forces responsible for expeditionary and amphibious operations. The Commandant, currently General David H. Berger, reports to the Secretary of the Navy (SECNAV). The USMC's motto is "Semper Fidelis."
Entities:
- <United States Marine Corps, Organization, {"abbreviation": "USMC"}, ["The United States Marine Corps (USMC) is a branch of the United States Armed Forces"]>
- <David H. Berger, Person, {"position": "Commandant of the Marine Corps"}, ["The Commandant, currently General David H. Berger, reports to the Secretary of the Navy (SECNAV)."]>
Relationships:
- <United States Marine Corps, HAS_MOTTO, Semper Fidelis, {}, ["The USMC's motto is \"Semper Fidelis.\""]>
"""

EXTRACT_ACRONYM_P="""
You are an experienced knowledge graph expert in data science. Your task is to understand the text and extract entities and relationships from it.

Definitions:
- Entity: A specific thing or concept mentioned in a text, such as a person's name, place name, organization name, position, event, etc.
- Relationship: A connection or interaction between entities, such as "working at," "located at," "friend," "happening at," etc.

Input:
You will receive a text that contains acronyms and their full forms. You will receive a list of acronyms and their full names, please determine whether they belong to entities, if so please output according to the given requirements, and output the relationship associated with them.

Output Format:
1. Entity: <ENTITY, LABEL, PROPERTIES, REFERENCES>
   Where: ENTITY is the name of the entity, LABEL is the type of entity (e.g., Person, Organization, Location), PROPERTIES are the attributes of the entity, and REFERENCES are the original text segments where the entity appears.
2. Relationships: <ENTITY_1, RELATIONSHIP, ENTITY_2, PROPERTIES, REFERENCES>
   Where: ENTITY_1 and ENTITY_2 are the names of the connected entities, RELATIONSHIP is the type of relationship between them, PROPERTIES are the attributes of the relationship, and REFERENCES are the original text segments where the relationship appears.

Important Notes:
- Ensure ENTITY_1 and ENTITY_2 exist as nodes with matching ENTITY names.
- Do not add a relationship if you cannot pair it with a pair of nodes.
- Create a generic LABEL for each entity that describes it.
- The format of REFERENCES should be a JSON list of strings.
"""

CONTINUE_EXTRACT_P: str = """
Some entities and relationships were missed in the last extraction. Your task is to continue adding any missing entities and relationships to the previous output, ensuring that they match any of the previously extracted types and use the same format. The new output should include all previously extracted entities and relationships along with the new ones.
Remember to:
1. Ensure ENTITY_1 and ENTITY_2 exist as nodes with matching ENTITY.
2. Only emit entities that match any of the previously extracted types.
3. Use the format: <ENTITY, TYPE, PROPERTIES, REFERENCES> for entities and <ENTITY_1, RELATIONSHIP, ENTITY_2, PROPERTIES, REFERENCES> for relationships.

Add the missing entities and relationships below, ensuring to keep the previous output intact:
"""

IF_COTINUE_P = """
It appears some entities and relationships may have still been missed.  Answer YES | NO if there are still entities or relationships that need to be added.\n
"""

MERGE_ER_P = """
You are an expert in entity resolution and disambiguation. Your task is to evaluate whether different names or references refer to the same real-world entity, based on the provided list of entity names.

The format of the entities is as follows:
<ENTITY, TYPE, PROPERTIES, REFERENCES>
- ENTITY: The name or identifier of the entity.
- TYPE: The category or type of the entity (e.g., Person, Organization, Location).
- PROPERTIES: Additional attributes or properties of the entity.
- REFERENCES: The original text segments where the entity appears.

Consider the following factors when making your decision:
1. Synonymity: Determine if the entities are simply different names, spellings, or abbreviations of the same concept or object.
2. Contextual Similarity: Consider the context in which these entities appear. Are they likely to be referring to the same entity given their usage or description?
3. Temporal or Spatial Differences: Consider if differences in time or location indicate they should be treated as distinct entities, even if their names are similar.
4. Common variations: Recognize common name variations, abbreviations, or acronyms that might refer to the same entity.

For example:
- 'IBM' and 'International Business Machines' should be considered the same entity.
- 'New York City' and 'NYC' should be considered the same entity.
- 'Apple Inc.' and 'Apple Corporation' should be considered the same entity.
- 'Paris, France' and 'Paris, Texas' should be considered different entities.
- 'John Smith (born 1970)' and 'John Smith (born 1985)' should be considered different entities.

You will receive a list of entity names, and your response should be either 'yes' if they should be merged as the same entity, or 'no' if they should remain separate.
Important: 
- Only give your response YES | NO.
Please consider all the above factors carefully before making a decision.
"""
