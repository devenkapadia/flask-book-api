import pickle
import numpy as np
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

pt = pickle.load(open('pt.pkl','rb'))
books = pickle.load(open('books.pkl','rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))

authors = pickle.load(open('authors.pkl','rb'))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get('/')
def home():
    return {'message': 'Welcome to our website!'}


@app.get('/data')
def sendData():
    with open('popular.pkl', 'rb') as file:
        data = pickle.load(file)
    
    data_list = data.to_dict(orient='records')
    return data_list
    # return jsonify(data_list)

@app.get('/get_authors')
def get_authors():
    author_book_counts = authors['Book-Author'].value_counts()
    authors_with_more_than_6_books = author_book_counts[author_book_counts >= 6].index

    filtered_books = authors[authors['Book-Author'].isin(authors_with_more_than_6_books)]

    author_avg_ratings = filtered_books.groupby('Book-Author')['Book-Rating'].mean().sort_values(ascending=False).reset_index()

    # Extract unique authors based on average rating
    unique_authors = author_avg_ratings.head(100)['Book-Author'].tolist()

    return {'unique_authors':unique_authors}

@app.post('/get_top_books')
def get_top_books(author: str):
    # data = request.get_json()
    # author = data.get('author')
    
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
    
    return {'Top Books':top_books_list}

@app.post('/recommend_books')
def recommend(user_input: str):
    # data = request.get_json()
    # user_input = data.get('user_input')

    # Find indices where pt.index contains the user_input as a substring
    matching_indices = pt.index[pt.index.str.contains(user_input, case=False)]

    if len(matching_indices) == 0:
        # return jsonify({'error': 'No matching books found'}), 404
        return {'error': 'No matching books found'}

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
    # return jsonify(recs)
    return {'Recommendations':recs}

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8000)
