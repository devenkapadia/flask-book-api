from flask import Flask, jsonify, request
from flask_cors import CORS
import pickle
import numpy as np

pt = pickle.load(open('pt.pkl','rb'))
books = pickle.load(open('books.pkl','rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))

authors = pickle.load(open('authors.pkl','rb'))

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return 'Welcome to our website!'


@app.route('/data')
def sendData():
    with open('popular.pkl', 'rb') as file:
        data = pickle.load(file)
    
    data_list = data.to_dict(orient='records')
    return jsonify(data_list)

@app.route('/get_authors', methods=['GET'])
def get_authors():
    author_book_counts = authors['Book-Author'].value_counts()
    authors_with_more_than_6_books = author_book_counts[author_book_counts >= 6].index

    filtered_books = authors[authors['Book-Author'].isin(authors_with_more_than_6_books)]

    author_avg_ratings = filtered_books.groupby('Book-Author')['Book-Rating'].mean().sort_values(ascending=False).reset_index()
    # Extract unique authors based on average rating
    unique_authors = author_avg_ratings.head(100)['Book-Author'].tolist()
    return jsonify(unique_authors)

@app.route('/get_top_books', methods=['POST'])
def get_top_books():
    data = request.get_json()
    author = data.get('author')
    
    # Filter the DataFrame for the selected author
    author_books = authors[authors['Book-Author'] == author]
    
    # Sort the books by rating
    sorted_books = author_books.sort_values(by='Book-Rating', ascending=False)
    
    # Use a set to track seen ISBNs to avoid duplicates
    seen_isbns = set()
    top_books_list = []

    for _, book in sorted_books.iterrows():
        isbn = book['ISBN']
        if isbn not in seen_isbns:
            top_books_list.append(book.to_dict())
            seen_isbns.add(isbn)
        if len(top_books_list) == 6:  
            break
    
    return jsonify(top_books_list)

@app.route('/recommend_books', methods=['POST'])
def recommend():
    data = request.get_json()
    user_input = data.get('user_input')

    # Find indices where pt.index contains the user_input as a substring
    matching_indices = pt.index[pt.index.str.contains(user_input, case=False)]

    if len(matching_indices) == 0:
        return jsonify({'error': 'No matching books found'}), 404

    # Get up to 5 recommendations for each matching index
    recs = []
    seen_books = set()
    for index in matching_indices:
        index_pos = np.where(pt.index == index)[0][0]
        similar_items = sorted(list(enumerate(similarity_scores[index_pos])), key=lambda x: x[1], reverse=True)[1:6]

        for i in similar_items:
            item = {}
            temp_df = books[books['Book-Title'] == pt.index[i[0]]]
            if not temp_df.empty:
                book_title = temp_df['Book-Title'].values[0]
                if book_title not in seen_books:
                    item['Book-Title'] = temp_df['Book-Title'].values[0]
                    item['Book-Author'] = temp_df['Book-Author'].values[0]
                    item['Image-URL-M'] = temp_df['Image-URL-M'].values[0]
                    recs.append(item)
                    seen_books.add(book_title)
                    if len(recs) == 6:  # Limit to 5 recommendations
                        break
        if len(recs) == 6:  # Limit to 5 recommendations
            break
    # Return JSON response using jsonify
    return jsonify(recs)

if __name__ == "__main__":
    app.run(debug=True)
