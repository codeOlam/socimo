import pandas as pd
import re
import spacy
import en_core_web_sm
from nltk.tokenize import RegexpTokenizer, WhitespaceTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import string

from app import db
from app.models import Post, User
import app.setwords as sw


nlp = en_core_web_sm.load()
tokenizer = RegexpTokenizer(r'\w+')
lemmatizer = WordNetLemmatizer()
stop_word = set(stopwords.words('english'))
punctuate = list(string.punctuation)
stop_word.update(punctuate)
word_tokenizer = WhitespaceTokenizer() 


def post_to_df():
	"""
	This function will get post queries and convert to 
	pd dataframe
	"""
	# get queries of all post and store in pd_dataframe
	#Defining the query
	# post_query = db.session.query(Post).with_entities(Post.user_id, Post.content)
	post_query = qs = db.session.query(User.name, Post.content).join(User)
	print('Post Query\n',post_query)

	#getting all post entries
	post_qs = post_query.all()
	print('Post Query Set\n',post_qs)

	#Provide alternate col name and set index
	# posts_to_df = pd.DataFrame.from_records(post_qs, 
	# 									index='name', 
	# 									columns=['name','content'])
	posts_to_df = pd.DataFrame([(d.name, d.content) for d in post_qs], columns=['name', 'content'])
	print('Post DataFrame\n', posts_to_df)

	return posts_to_df


post_df = post_to_df()


def clean_post(df, text):
	"""
	This function will clean post, removing unnecessary characters
	That will affect classification and clustering.
	"""
	#Convert all case to lower case.
	df[text] = df[text].str.lower()
	print('post_df.lower()\n', df[text])
	
	#Remove all unnecessary characters
	df[text] = df[text].apply(lambda elem: re.sub(r"(@[A-Za-z0–9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|^rt|http.+?",
			"",
			elem))
	print('df[text]\n', df[text])

	return df

post_df = clean_post(post_df, 'content')


def tidy_up(text):
	"""
	This function will Tokenize posts splitting string into list
	remove stop words and reduce words to their root form by lemmatization 
	"""
	final_text = []
	for i in word_tokenizer.tokenize(text):
		if i.lower() not in stop_word:
			word = lemmatizer.lemmatize(i)
			final_text.append(word.lower())

	return " ".join(final_text)

post_df.content =post_df.content.apply(tidy_up)


#Cleaning up setwords
health = tidy_up(sw.health_related_words)
politics = tidy_up(sw.politics_related_words)
security = tidy_up(sw.security_related_words)
economic = tidy_up(sw.economic_related_words)

#Dropping duplicates
words =  health.split()
health = " ".join(sorted(set(words), key=words.index))

words = politics.split()
politics = " ".join(sorted(set(words), key=words.index))

words = security.split()
security = " ".join(sorted(set(words), key=words.index))

words = economic.split()
economy = " ".join(sorted(set(words), key=words.index))



#Implementing Jaccard SImilarity
def jaccard_similarity(q, doc):
	intersect = set(q).intersection(set(doc))
	union = set(q).union(set(doc))

	# print('\nlen(intersect)/len(union)', len(intersect)/len(union), '\n')

	return len(intersect)/len(union)


#Implementing Similarity Score
def sim_scores(group, content):
	points = []
	for post in content:
		s = jaccard_similarity(group, post)
		points.append(s)

	# print('\nFrom sim_scores', points)
	return points

#Comparing Post contents using jaccard similarity and 
#Getting scores of all cluster points
h_points = sim_scores(health, post_df.content.to_list())
p_points = sim_scores(politics, post_df.content.to_list())
s_points = sim_scores(security, post_df.content.to_list())
e_points = sim_scores(economy, post_df.content.to_list())

#Creating a DF for Jaccard Scores
data = {'names': post_df.name.to_list(),
		'health_point':h_points,
		'politics_point':p_points,
		'security_point':s_points,
		'economic_point':e_points}

points_df = pd.DataFrame(data)
print('')
print('data\n',points_df)

#Assigining Categories based on Highest point
def fetch_cate(h1,h2,h3,h4):
	heal = []
	poli = []
	sec = []
	eco = []

	for a, b, c, d in zip(h1, h2, h3, h4):
		m = max(a, b, c, d)
		if m == a:
			heal.append(1)
		else:
			heal.append(0)
		if m == b:
			poli.append(1)
		else:
			poli.append(0)
		if m == c:
			sec.append(1)
		else:
			sec.append(0)
		if eco == d:
			eco.append(1)
		else:
			eco.append(0)

	return heal, poli, sec, eco

h1 = points_df.health_point.to_list()
h2 = points_df.politics_point.to_list()
h3 = points_df.security_point.to_list()
h4 = points_df.economic_point.to_list()

heal, poli, sec, eco = fetch_cate(h1, h2, h3, h4)

data = {'name': points_df.names.to_list(),
		'health':heal,
		'politics': poli,
		'security': sec,
		'economic': eco}


cate_df = pd.DataFrame(data)

print('\ncategory\n', cate_df, '\n')

#Grouping Post by user
u_group_df = cate_df.groupby(['name']).sum()
print('\n\t\t\tGrouping by user\n', u_group_df, '\n')

#Adding a new column Total to get sum of user post
u_group_df['total_post'] = u_group_df['health'] + u_group_df['politics'] + \
					u_group_df['security'] + u_group_df['economic']

print('\n\t\t\tDataFrame\n', u_group_df, '\n')


#Adding a new row to get total posts in df
u_group_df.loc["Total"] = u_group_df.sum()

print('\n\t\t\tFinished DataFrame\n', u_group_df, '\n')