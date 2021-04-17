import pandas as pd
import re
import spacy
import en_core_web_sm
from nltk.tokenize import RegexpTokenizer, WhitespaceTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import string
from sklearn.cluster import KMeans
import numpy as np
import sklearn.metrics as metrics
from scipy.spatial import distance

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
	post_query = qs = db.session.query(User.id, User.name, Post.content).join(User)
	# print('Post Query\n',post_query)

	#getting all post entries
	post_qs = post_query.all()
	# print('Post Query Set\n',post_qs)

	posts_to_df = pd.DataFrame([(d.id, d.name, d.content) for d in post_qs], columns=['user_id', 'name', 'content'])
	print('Post DataFrame\n', posts_to_df)

	return posts_to_df


def clean_post(df, text):
	"""
	This function will clean post, removing unnecessary characters
	That will affect classification and clustering.
	"""
	#Convert all case to lower case.
	df[text] = df[text].str.lower()
	# print('post_df.lower()\n', df[text])
	
	#Remove all unnecessary characters
	df[text] = df[text].apply(lambda elem: re.sub(r"(@[A-Za-z0–9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|^rt|http.+?",
			"",
			elem))
	# print('df[text]\n', df[text])

	return df


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


#Cleaning up setwords
def clean_setwords():

	health = tidy_up(sw.health_related_words)
	politics = tidy_up(sw.politics_related_words)
	security = tidy_up(sw.security_related_words)
	economy = tidy_up(sw.economic_related_words)

	#Dropping duplicates
	words =  health.split()
	health = " ".join(sorted(set(words), key=words.index))

	words = politics.split()
	politics = " ".join(sorted(set(words), key=words.index))

	words = security.split()
	security = " ".join(sorted(set(words), key=words.index))

	words = economy.split()
	economy = " ".join(sorted(set(words), key=words.index))

	return health, politics, security, economy



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


#Assigining Categories based on Highest point
def fetch_cate(h1, h2, h3, h4):
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


def set_clst_to_df(he, pol, se, ec, cn):
	post_df = post_to_df()
	post_df_ = clean_post(post_df, 'content')
	post_df_.content =post_df_.content.apply(tidy_up)
	post_clean_list = post_df_.content.to_list()

	heal_ = ['h' if h >=1 else h for h in he]
	poli_ = ['p' if p >=1 else p for p in pol]
	sec_ = ['s' if s >=1 else s for s in se]
	eco_ = ['ec' if ec >=1 else ec for ec in ec]

	print('heal_: ', len(heal_))
	print('poli_: ', len(poli_))
	print('sec_: ', len(sec_))
	print('eco_: ', len(eco_))
	print('user_id: ', len(post_df.user_id.to_list()))
	print('User_name: ', len(post_df["name"]))
	print('Cluster_Num: ', len(cn))
	print('post_clean_list: ', ' : ', len(post_clean_list))


	cluster_post_data = {'user_id': post_df.user_id.to_list(),
					'User_name': post_df["name"],
					# 'Post': post_df["content"],
					'Cluster_Num': cn,
					'Cleaned_Post': post_clean_list,
					'health':heal_,
					'politics': poli_,
					'security': sec_,
					'economic': eco_
					}

	# print('\ncluster_post_data: \n', cluster_post_data)
	#set to df
	clst_post_df = pd.DataFrame(cluster_post_data)
	print('\nCluster in DF\n',clst_post_df)

	return clst_post_df


# #Grouping Cluster by number
# cluster_gp = cluster_post_df.groupby('User_name').sum()
# print('\n\t\t**************Grouping Cluster By Number*******************\n', cluster_gp)

def kmean_clst():
	print('\n\t\t***************K-MEAN Algorithm Implementation*******************')

	n_clst = 4

	kmeans = KMeans(n_clusters=n_clst, 
					init='k-means++', 
					random_state=0, 
					max_iter=100, 
					n_init=10,
					verbose=True)

	print('\nChecking if this will refresh the db\n')
	post_df = post_to_df()
	print('\nRefreshing db...\n', post_to_df)
	print('')

	post_df_ = clean_post(post_df, 'content')
	post_df_.content =post_df_.content.apply(tidy_up)
	post_clean_list = post_df_.content.to_list()

	health, politics, security, economy = clean_setwords()

	#Comparing Post contents using jaccard similarity and 
	#Getting scores of all cluster points
	h_points = sim_scores(health, post_df_.content.to_list())
	p_points = sim_scores(politics, post_df_.content.to_list())
	s_points = sim_scores(security, post_df_.content.to_list())
	e_points = sim_scores(economy, post_df_.content.to_list())

	data = {'user_id': post_df.user_id.to_list(),
		'names': post_df.name.to_list(),
		'health_point':h_points,
		'politics_point':p_points,
		'security_point':s_points,
		'economic_point':e_points}

	points_df = pd.DataFrame(data)

	h1_ = points_df.health_point.to_list()
	h2_ = points_df.politics_point.to_list()
	h3_ = points_df.security_point.to_list()
	h4_ = points_df.economic_point.to_list()


	heal, poli, sec, eco = fetch_cate(h1_, h2_, h3_, h4_)

	#Setting Data for K-mean fitting
	k_data = {'health':heal,
		'politics': poli,
		'security': sec,
		'economic': eco}

	k_data_df = pd.DataFrame(k_data).values

	# Compute k-means clustering.
	kmeans = kmeans.fit(k_data_df)

	#Using the k-mean to predict the context of the post
	# Predict the closest cluster each word in Post belongs to
	cluster_num = kmeans.predict(k_data_df)	

	cn = cluster_num
	print ('\ncluster number: ', cn)

	cluster_post_df = set_clst_to_df(heal, poli, sec, eco, cn)
	try:
		heal_cluster_group = cluster_post_df.groupby('Cluster_Num')
		get_heal_cluster = heal_cluster_group.get_group(0)
		print('\n\t\t**************Health_cluster_group*******************\n', get_heal_cluster)
	except KeyError:
		print('\n\t\t**************Health_cluster_group*******************\n')
		print('\nNo posts Found in this Cluster!')

	try:	
		poli_cluster_group = cluster_post_df.groupby('Cluster_Num')
		get_poli_cluster = poli_cluster_group.get_group(1)
		print('\n\t\t**************Politics_cluster_group*******************\n', get_poli_cluster)
	except KeyError:
		print('\n\t\t**************Politics_cluster_group*******************\n')
		print('\nNo posts Found in this Cluster!')

	try:
		sec_cluster_group = cluster_post_df.groupby('Cluster_Num')
		get_sec_cluster = sec_cluster_group.get_group(2)
		print('\n\t\t**************Security_cluster_group*******************\n', get_sec_cluster)
	except KeyError:
		print('\n\t\t**************Security_cluster_group*******************\n')
		print('\nNo posts Found in this Cluster!')

	try:
		eco_cluster_group = cluster_post_df.groupby('Cluster_Num')
		get_eco_cluster = eco_cluster_group.get_group(3)
		print('\n\t\t**************Economy_cluster_group*******************\n', get_eco_cluster)
	except KeyError:
		get_eco_cluster = ''
		print('\n\t\t**************Economy_cluster_group*******************\n')
		print('\nNo posts Found in this Cluster!')

	return get_heal_cluster, get_poli_cluster, get_sec_cluster, get_eco_cluster