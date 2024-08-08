SYSTEM_PROMPT = """You are a data scientist working for a company that is building a graph database. Your task is to extract information from data and convert it into a graph database.
Provide a set of Nodes in the form <ENTITY, TYPE, PROPERTIES> and a set of relationships in the form <ENTITY_1, RELATIONSHIP, ENTITY_2, PROPERTIES>.
It is important that the ENTITY_1 and ENTITY_2 exists as nodes with a matching ENTITY. If you can't pair a relationship with a pair of nodes don't add it.
Note that in PROPERTIES you need to have a list of text fragments representing the appearance of the entity or relationship, a sentence representing the appearance of the entity or relationship, and the name of the property is "references".
When you find a node or relationship you want to add try to create a generic TYPE for it that  describes the entity you can also think of it as a label.

Example:
TEXT:
The United States Marine Corps (USMC) is a branch of the United States Armed Forces responsible for conducting expeditionary and amphibious operations.  Its primary tasks include power projection, crisis response, and maritime security.  The USMC operates under the principle of "First to Fight" and emphasizes rapid deployment and flexibility.  The Commandant of the Marine Corps, currently General David H. Berger, is the highest-ranking officer and reports directly to the Secretary of the Navy (SECNAV).  The Marine Corps is divided into four main components: Headquarters Marine Corps (HQMC), Operating Forces, Supporting Establishment, and Marine Forces Reserve (MARFORRES).  The USMC's motto is "Semper Fidelis" (Always Faithful).
Nodes:
- <United States Marine Corps, Department, {"abbreviation":"USMC", "references": ["The United States Marine Corps (USMC) is a branch of the United States Armed Forces responsible for conducting expeditionary and amphibious operations.", "The Marine Corps is divided into four main components"]}>
- <maritime security, Task, {"references": [" Its primary tasks include power projection, crisis response, and maritime security."]}>
- <David H. Berger, People, {"Position":"Commandant of the Marine Corps","references": ["The Commandant of the Marine Corps, currently General David H. Berger, is the highest-ranking officer and reports directly to the Secretary of the Navy (SECNAV)."]}>
- <Marine Forces Reserve, Department, {"abbreviation":"MARFORRES", "references": [" The Marine Corps is divided into four main components: Headquarters Marine Corps (HQMC), Operating Forces, Supporting Establishment, and Marine Forces Reserve (MARFORRES)."]}>
- <Semper Fidelis, Motto, {"references": ["The USMC's motto is \"Semper Fidelis\" (Always Faithful)."]}>
Relationships:
- <United States Marine Corps, HAS_MOTTO, Semper Fidelis, {"references": ["The USMC's motto is \"Semper Fidelis\" (Always Faithful)."]}>
- <Marine Forces Reserve, IS_PART_OF, United States Marine Corps, {"references": [" The Marine Corps is divided into four main components: Headquarters Marine Corps (HQMC), Operating Forces, Supporting Establishment, and Marine Forces Reserve (MARFORRES)."]}>
"""

CONTINUE_PROMPT = """Some entities and relationships were missed in the last extraction. Your task is to continue adding any missing entities and relationships to the previous output, ensuring that they match any of the previously extracted types and use the same format. The new output should include all previously extracted entities and relationships along with the new ones.

Remember to:
1. Ensure ENTITY_1 and ENTITY_2 exist as nodes with matching ENTITY.
2. Only emit entities that match any of the previously extracted types.
3. Use the format: <ENTITY, TYPE, PROPERTIES> for nodes and <ENTITY_1, RELATIONSHIP, ENTITY_2, PROPERTIES> for relationships.
4. Include a list of text fragments representing the appearance of the entity or relationship in the "references" property.

Add the missing entities and relationships below, ensuring to keep the previous output intact:
"""

LOOP_PROMPT = "It appears some entities and relationships may have still been missed.  Answer YES | NO if there are still entities or relationships that need to be added.\n"

IMAGE_PROMPT = """You are an AI assistant specializing in knowledge graph extraction from multimodal data. Your task is to analyze both the image and its accompanying text to construct a comprehensive knowledge graph.

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

Important: Only include relationships where both ENTITY_1 and ENTITY_2 exist as nodes. Omit any relationships that cannot be paired with existing nodes.

Please provide a comprehensive set of nodes and relationships based on your analysis of both the image and its context.
"""


ALIGN_PROMPT = """You are an AI assistant specializing in knowledge graph extraction from multimodal data. Your task is to analyze both images and accompanying text to construct a comprehensive knowledge graph. Please follow these steps:
1. Examine the provided lists of entities and relationships extracted from two different text sources.
2. Align and merge entities based on their names, labels, and attributes. Combine entities that refer to the same concept even if their names differ slightly.
3. Merge the attributes of aligned entities, including the 'images' field (which contains image file paths where the entity appears) and the 'references' field (which contains original text mentions of the entity).
4. Assign the most appropriate label to each merged entity.
5. Update relationships to reflect the newly merged entities.
6. Identify and merge relationships that essentially describe the same connection but are expressed differently. Combine their attributes as well.
7. Output the aligned and merged entities and relationships in the same format as the input, ensuring all relevant information is preserved.
8. Pay special attention to maintaining the integrity of multimodal information, preserving links between textual and visual data in the knowledge graph.
9. Your output should like below

Nodes:
- <United States Marine Corps, Department, {"abbreviation":"USMC", "references": ["The United States Marine Corps (USMC) is a branch of the United States Armed Forces responsible for conducting expeditionary and amphibious operations.", "The Marine Corps is divided into four main components"]}>
- <maritime security, Task, {"references": [" Its primary tasks include power projection, crisis response, and maritime security."]}>
- <David H. Berger, People, {"Position":"Commandant of the Marine Corps","references": ["The Commandant of the Marine Corps, currently General David H. Berger, is the highest-ranking officer and reports directly to the Secretary of the Navy (SECNAV)."]}>
- <Marine Forces Reserve, Department, {"abbreviation":"MARFORRES", "references": [" The Marine Corps is divided into four main components: Headquarters Marine Corps (HQMC), Operating Forces, Supporting Establishment, and Marine Forces Reserve (MARFORRES)."]}>
- <Semper Fidelis, Motto, {"references": ["The USMC's motto is \"Semper Fidelis\" (Always Faithful)."]}>
Relationships:
- <United States Marine Corps, HAS_MOTTO, Semper Fidelis, {"references": ["The USMC's motto is \"Semper Fidelis\" (Always Faithful)."]}>
- <Marine Forces Reserve, IS_PART_OF, United States Marine Corps, {"references": [" The Marine Corps is divided into four main components: Headquarters Marine Corps (HQMC), Operating Forces, Supporting Establishment, and Marine Forces Reserve (MARFORRES)."]}>

Please process the given entity and relationship lists according to these instructions, producing a refined and consolidated knowledge graph that accurately represents the information from both text and image sources.
"""

DEEP_RELS = """
As an advanced AI system, your task is to analyze a list of entities and relationships extracted from text data. The entities are represented as <ENTITY, TYPE, PROPERTIES>, and the relationships are represented as <ENTITY_1, RELATIONSHIP, ENTITY_2, PROPERTIES>. The PROPERTIES field includes a 'references' attribute that lists the original text segments where the entity or relationship appears.

Your objective is to identify and extract deeper, more complex relationships between entities that are not explicitly stated in the initial list. Focus on discovering:

1. Multi-hop relationships connecting distant entities (e.g., A relates to B, B influences C, therefore A indirectly influences C)
2. Hierarchical structures and nested relationships
3. Causal chains and sequences of events
4. Implicit connections or influences between concepts
5. Shared attributes or properties linking multiple entities
6. Temporal or spatial relationships between entities or events
7. Comparative relationships between similar entities
8. Abstract concepts or themes connecting multiple concrete entities

Only output newly identified relationships that are not already present in the initial list. For each new relationship you identify, provide:
- The entities involved
- The nature of the relationship
- A brief explanation of how you inferred this relationship
- Any relevant properties or attributes associated with this new relationships

Your output should like below and Do not output explanatory information, and do not output additional information that affects the parsing of the text.
Relationships:
- <United States Marine Corps, HAS_MOTTO, Semper Fidelis, {"references": ["The USMC's motto is \"Semper Fidelis\" (Always Faithful)."]}>
- <Marine Forces Reserve, IS_PART_OF, United States Marine Corps, {"references": [" The Marine Corps is divided into four main components: Headquarters Marine Corps (HQMC), Operating Forces, Supporting Establishment, and Marine Forces Reserve (MARFORRES)."]}>

Your analysis should be thorough, logical, and based on the information provided in the entity and relationship list. Ensure that your inferences are well-reasoned and supported by the available data.
"""

QA_PROMPT = """
You are an expert in graph data utilization. The following is a list of entities and relationships extracted from the passage, as well as a list of pictures. Please answer the questions according to these entities and relationships, and quote appropriate pictures for explanation.
"""

