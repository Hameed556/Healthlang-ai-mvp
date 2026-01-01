"""
Simple script to populate ChromaDB with basic medical knowledge
"""
import chromadb
from pathlib import Path

# Initialize ChromaDB
chroma_path = Path("./data/chroma")
chroma_path.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(chroma_path))

# Create or get collection
try:
    collection = client.get_collection(name="medical_docs")
    print(f"Collection 'medical_docs' already exists with {collection.count()} documents")
except:
    collection = client.create_collection(
        name="medical_docs",
        metadata={"description": "Medical knowledge base"}
    )
    print("Created new collection 'medical_docs'")

# Sample medical documents
medical_docs = [
    {
        "id": "malaria_1",
        "text": "Malaria is a serious disease caused by a parasite transmitted through mosquito bites. Common symptoms include high fever, chills, sweating, headache, muscle aches, nausea, and vomiting. In severe cases, it can cause organ failure. Prevention includes using mosquito nets, insect repellent, and antimalarial medications when traveling to high-risk areas.",
        "metadata": {"topic": "malaria", "source": "medical_guidelines"}
    },
    {
        "id": "diabetes_1",
        "text": "Diabetes is a chronic condition affecting blood sugar regulation. Type 1 diabetes occurs when the body doesn't produce insulin, while Type 2 diabetes occurs when the body becomes insulin resistant. Symptoms include increased thirst, frequent urination, extreme hunger, unexplained weight loss, fatigue, and blurred vision. Management includes diet, exercise, blood sugar monitoring, and medication.",
        "metadata": {"topic": "diabetes", "source": "medical_guidelines"}
    },
    {
        "id": "hypertension_1",
        "text": "High blood pressure (hypertension) is a condition where blood pressure remains elevated over time. It often has no symptoms but increases risk of heart disease, stroke, and kidney problems. Causes include genetics, poor diet, lack of exercise, obesity, excessive alcohol, and stress. Treatment involves lifestyle changes and medication.",
        "metadata": {"topic": "hypertension", "source": "medical_guidelines"}
    },
    {
        "id": "fever_1",
        "text": "Fever is a temporary increase in body temperature, often due to infection. Normal body temperature is around 98.6°F (37°C). A fever is generally considered 100.4°F (38°C) or higher. Common causes include viral infections, bacterial infections, heat exhaustion, and certain medications. Seek medical attention for very high fever (103°F+), persistent fever, or fever with severe symptoms.",
        "metadata": {"topic": "fever", "source": "medical_guidelines"}
    },
    {
        "id": "headache_1",
        "text": "Headaches are common and can have many causes. Tension headaches feel like pressure or tightness. Migraines cause severe throbbing pain, often with nausea and light sensitivity. Cluster headaches cause intense pain around one eye. Treatment depends on type and may include rest, hydration, pain relievers, or prescription medications. Seek immediate care for sudden severe headaches.",
        "metadata": {"topic": "headache", "source": "medical_guidelines"}
    },
    {
        "id": "covid_1",
        "text": "COVID-19 is caused by the SARS-CoV-2 virus. Symptoms range from mild to severe and include fever, cough, shortness of breath, fatigue, body aches, loss of taste or smell, sore throat, and congestion. Prevention includes vaccination, mask-wearing, hand hygiene, and social distancing. Seek medical care for difficulty breathing, persistent chest pain, or confusion.",
        "metadata": {"topic": "covid-19", "source": "medical_guidelines"}
    },
    {
        "id": "asthma_1",
        "text": "Asthma is a chronic respiratory condition causing airway inflammation and narrowing. Symptoms include wheezing, shortness of breath, chest tightness, and coughing, especially at night or during exercise. Triggers include allergens, exercise, cold air, and respiratory infections. Treatment includes quick-relief inhalers for symptoms and long-term control medications.",
        "metadata": {"topic": "asthma", "source": "medical_guidelines"}
    },
    {
        "id": "tuberculosis_1",
        "text": "Tuberculosis (TB) is a bacterial infection primarily affecting the lungs. Symptoms include persistent cough (lasting 3+ weeks), chest pain, coughing up blood, fatigue, weight loss, fever, and night sweats. TB spreads through airborne droplets. Treatment requires a long course of antibiotics (6-9 months). Early detection and treatment are crucial.",
        "metadata": {"topic": "tuberculosis", "source": "medical_guidelines"}
    }
]

# Add documents to collection
try:
    ids = [doc["id"] for doc in medical_docs]
    documents = [doc["text"] for doc in medical_docs]
    metadatas = [doc["metadata"] for doc in medical_docs]
    
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"✅ Successfully added {len(medical_docs)} medical documents to ChromaDB")
    print(f"Total documents in collection: {collection.count()}")
    
except Exception as e:
    print(f"❌ Error adding documents: {e}")
