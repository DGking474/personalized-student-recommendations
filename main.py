import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns

# API Endpoints
current_quiz_url = "https://api.jsonserve.com/XgAgFJ"
historical_quiz_url = "https://api.jsonserve.com/rJvd7g"

# Fetch Data Function
def fetch_data(url):
    """Fetch data from a given API URL."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data from {url}, status code: {response.status_code}")

# Load Data
try:
    current_quiz_data = fetch_data(current_quiz_url)
    historical_quiz_data = fetch_data(historical_quiz_url)
except Exception as e:
    print(f"Error loading data: {e}")
    raise

# Process Current Quiz Data
if isinstance(current_quiz_data, list):
    current_quiz_df = pd.DataFrame(current_quiz_data)
else:
    raise ValueError("Unexpected format for current_quiz_data: Expected a list.")

# Process Historical Quiz Data
if isinstance(historical_quiz_data, dict):
    if 'response_map' in historical_quiz_data:
        response_map = historical_quiz_data['response_map']
        historical_performance = pd.DataFrame([
            {'question_id': k, 'selected_option_id': v}
            for k, v in response_map.items()
        ])

        # Add dummy topic and correctness columns for demonstration
        historical_performance['topic'] = historical_performance['question_id'].apply(lambda x: f"Topic_{int(x) % 3}")
        historical_performance['correct'] = historical_performance['selected_option_id'].apply(lambda x: x % 2 == 0)
    else:
        raise ValueError("Key 'response_map' not found in historical_quiz_data.")

    # Extract Metadata
    historical_metadata = {key: historical_quiz_data[key] for key in [
        'score', 'accuracy', 'total_questions', 'correct_answers', 'incorrect_answers'
    ]}
else:
    raise ValueError("Unexpected format for historical_quiz_data: Expected a dictionary.")

# Calculate Topic-Wise Accuracy
def calculate_accuracy(df):
    if 'topic' in df.columns and 'correct' in df.columns:
        return df.groupby('topic').apply(
            lambda x: (x['correct'].sum() / len(x)) * 100
        ).reset_index(name='accuracy')
    else:
        return pd.DataFrame(columns=['topic', 'accuracy'])

# Current and Historical Accuracy
current_accuracy = calculate_accuracy(current_quiz_df)
historical_accuracy = calculate_accuracy(historical_performance)

# Merge data for trend analysis
if not current_accuracy.empty and not historical_accuracy.empty:
    merged_accuracy = pd.merge(
        historical_accuracy, current_accuracy, on='topic', suffixes=('_historical', '_current')
    )
    merged_accuracy['improvement'] = merged_accuracy['accuracy_current'] - merged_accuracy['accuracy_historical']
else:
    merged_accuracy = pd.DataFrame()

# Generate Recommendations
if not current_accuracy.empty:
    weak_topics = current_accuracy[current_accuracy['accuracy'] < 60]
    recommendations = [
        f"Focus on topic: {row['topic']} to improve accuracy."
        for _, row in weak_topics.iterrows()
    ]
else:
    recommendations = []

# Define Student Persona
def define_persona(accuracy_df):
    if accuracy_df['accuracy'].mean() > 80:
        return "Achiever: High accuracy, consistent performance."
    elif accuracy_df['accuracy'].mean() > 60:
        return "Improver: Making good progress."
    else:
        return "Learner: Needs to focus on weak areas."

persona = define_persona(current_accuracy) if not current_accuracy.empty else "Insufficient data to define persona."

# Visualize Topic-Wise Accuracy
plt.figure(figsize=(10, 6))
sns.barplot(data=current_accuracy, x='topic', y='accuracy', palette='viridis')
plt.title('Topic-Wise Accuracy in Current Quiz')
plt.xlabel('Topic')
plt.ylabel('Accuracy (%)')
plt.xticks(rotation=45)
plt.show()

# Display Insights
print("\nMerged Accuracy Trends:\n", merged_accuracy)
print("\nRecommendations:\n", "\n".join(recommendations))
print("\nStudent Persona:\n", persona)

# Save Recommendations to File
with open("recommendations.txt", "w") as f:
    f.write("\n".join(recommendations))
