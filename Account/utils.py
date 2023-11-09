import json
import random
from urllib import parse

from django.db.models import Q

from .models import User, Couple


def get_path(request):
	"""
    This function gets the current url
    :param request: HTTP request
    :return: it returns a string
    """
	return f'http://{str(request.get_host())}{str(request.get_full_path(True))}'


def _3_point(your_choice, choice):
	"""
    This function assigns a point to a variable that is equal to close to the desired variable.
    :param your_choice: the desired variable.
    :param choice: the variable to be tested.
    :return: it returns an integer point.
    """
	if str(your_choice) == 'Does Not Matter' or str(your_choice).isalpha():
		return 1

	if str(your_choice).isdigit():
		your_choice = int(your_choice)
	if str(choice).isdigit():
		choice = int(choice)
	if (your_choice == 0) or abs(your_choice - choice) == 0:
		return 1

	if abs(choice - your_choice) == 1:
		return 1 / 2

	return 0


def age_range(me, you):
	"""
    This function checks if a particular age falls into a specified range or close to the range.
    :param me: the person who specified the range.
    :param you: the person who has the age.
    :return: returns a point assigned to the age.
    """
	min_age = me.choice_data['min-age']
	max_age = me.choice_data['max-age']
	age = you.user_data['age']
	if int(age) in range(int(min_age), int(max_age)):
		return 1
	# grace of 4 years for each range
	elif abs(int(min_age) - int(age)) < 5 and abs(int(max_age) - int(age)) < 5:
		return 0.5
	else:
		return 0


def _2_point(minimum, maximum, choice):
	"""
    This function assigns a point to a choice based on how close it is to the minimum and the maximum.
    :param minimum:  maximum value.
    :param maximum:  minimum value or value specified by the other person.
    :param choice:  choice value.
    :return: it returns an integer point.
    """
	if str(choice).isdigit():
		choice = int(choice)
	if str(minimum).isdigit():
		minimum = int(minimum)
	if choice < minimum:
		return 0
	if minimum == 0:
		return 1
	total = (maximum - minimum) + 1
	point = (choice - minimum) + 1
	score = (point / total)
	return score


def compare_users(me, you):
	"""
    This function compares two users against each other to determine their compatibility.
    :param me: first user.
    :param you: second user.
    :return: it returns the percentage of their compatibility.
    """
	mark = 0
	absolute_match = ('residence_lga', 'residence_state', 'origin_lga',
	                  'origin_state', 'denomination', 'religion', 'marital_status', 'children',
	                  'blood_group', 'genotype')

	_2_spectrum = ('net_worth', 'education', 'body_shape')

	_3_spectrum = ('complexion', 'height', 'body_type', 'drink', 'smoke', 'conscientiousness', 'openess',
	               'extraversion', 'agreeableness', 'neurotism')
	deal_breakers = me.deal_breaker
	total = len(absolute_match) + len(_3_spectrum) + len(_2_spectrum) + 1

	for i in deal_breakers:
		if i == 'No Dealbreaker':
			continue
		try:
			if str(me.choice_data[i]) == str(you.user_data[i]):
				mark += 1
			else:
				return 0
		except KeyError:
			continue

	for i in absolute_match:
		try:
			if str(you.user_data[i]) in str(me.choice_data[i]) \
					or 'Does Not Matter' == str(me.choice_data[i]):
				mark = mark + 1
		except KeyError:
			continue

	for i in _2_spectrum:
		try:
			if str(me.choice_data[i]) == 'Does Not Matter':
				mark = mark + 1
			else:
				mark = mark + _2_point(me.choice_data[i], 5, you.user_data[i])
		except KeyError:
			continue

	for i in _3_spectrum:
		try:
			mark = mark + _3_point(me.choice_data[i], you.user_data[i])
		except KeyError:
			continue
	try:
		mark = mark + age_range(me, you)
	except KeyError:
		pass
	return (mark / total) * 100


def match_user(user):
	"""
    This function matches a particular user to other users based on the compatibility scores.
    :param user:  The user instance.
    :return:  it is a void.
    """
	success_list = {}
	no_list = []
	# filter users
	gender = "male" if str(user.sex).lower() == "female" else "female"
	all_users = User.objects.filter(Q(~Q(id__in=user.jilted_matches)
	                                  & ~Q(id__in=user.no_matches) &
	                                  ~Q(user_data=dict())),
	                                sex__iexact=gender, can_be_matched=True).only('id')
	all_users = (user for user in all_users if not user.complete_match and not user.is_couple)
	# compare filtered users with user and return matches

	for second_user in all_users:
		print("second user: ", second_user)
		peep_score = compare_users(user, second_user)
		my_score = compare_users(second_user, user)
		try:
			if peep_score >= 50 and my_score >= 50:
				success_list[second_user.id] = peep_score
			else:
				no_list.append(str(second_user.id))
		except KeyError:
			no_list.append(str(second_user.id))
	success_list = sorted(success_list.items(), key=lambda x: x[1], reverse=True)
	print("success_list: ", success_list)
	user.successful_matches = success_list
	user.no_matches = no_list
	user.save()


def lucky_draw(num):
	"""
    This function randomly selects the specified number of couples from the database tables.
    :param num: The number of couples to be selected.
    :return:  returns a list of selected couples.
    """
	lucky_ones = []
	couples = Couple.objects.all()
	for i in range(num):
		random.shuffle(couples)
		lucky_ones.append(couples[0])
	return tuple(lucky_ones)


def get_username():
	"""
    This function generates a random username for a particular user.
    :return: a string => the username
    """
	username = f'Datefix-User-{str(random.randint(1, 123456789))}'
	if User.objects.filter(username__iexact=username).exists():
		return get_username()
	return username


def flash(request, message, status, icon=None):
	"""
    This function sets the variables for the alert on a page.
    :param request: The HTTP request
    :param message: The message to be displayed on the alert bar.
    :param status: The status e.g warning, success or danger
    :param icon: The icon to be displayed
    :return: it returns nothing
    """
	request.session['message'] = message
	request.session['status'] = status
	if status == "success":
		icon = 'thumbs-up'
	elif status == "warning":
		icon = icon
	elif status == "info":
		icon = "info-icon"
	else:
		icon = "remove-icon"
	request.session['icon'] = icon
	return


category_1 = ({
	              'Question': 'I often do not feel I have to justify myself to people',
	              'Weight': 1,
	              'Category': ''
              },
              {
	              'Question': 'I prefer not to engage with people who seem angry or upset',
	              'Weight': -1
              },
              {
	              'Question': 'I do not usually initiate conversations',
	              'Weight': -1
              },
              {
	              'Question': 'I feel comfortable around people',
	              'Weight': 1
              },
              {
	              'Question': 'I keep in the background',
	              'Weight': -1
              },
              {
	              'Question': 'I would rather improvise than spend time coming up with a detailed plan',
	              'Weight': 1
              },
              {
	              'Question': 'I find it easy to walk up to a group of people and join in conversation',
	              'Weight': 1
              },
              {
	              'Question': 'I don\'t like to draw attention to myself',
	              'Weight': -1
              },
              {
	              'Question': 'I care more about making sure no one gets upset than winning a debate',
	              'Weight': 1
              },
              {
	              'Question': 'I get so lost in my thoughts I ignore or forget my surroundings',
	              'Weight': -1
              },
)
category_2 = ({
	              'Question': 'I get stressed out easily',
	              'Weight': 1
              },
              {
	              'Question': 'I am relaxed most of the time',
	              'Weight': -1
              },
              {
	              'Question': 'I worry about things',
	              'Weight': 1
              },
              {
	              'Question': 'I seldom feel blue',
	              'Weight': -1
              },
              {
	              'Question': 'I am easily disturbed',
	              'Weight': 1
              },
              {
	              'Question': 'I get upset easily',
	              'Weight': 1
              },
              {
	              'Question': 'I change my mood a lot',
	              'Weight': 1
              },
              {
	              'Question': 'I have frequent mood swings',
	              'Weight': 1
              },
              {
	              'Question': 'I get irritated easily',
	              'Weight': 1
              },
              {
	              'Question': 'I often feel blue',
	              'Weight': 1
              },
)
category_3 = ({
	              'Question': 'I feel little concern for others',
	              'Weight': -1
              },
              {
	              'Question': 'I am interested in people',
	              'Weight': 1
              },
              {
	              'Question': 'I insult people',
	              'Weight': -1
              },
              {
	              'Question': 'I sympathize with others\' feelings',
	              'Weight': 1
              },
              {
	              'Question': 'I am not interested in other people\'s problems',
	              'Weight': -1
              },
              {
	              'Question': 'I have a soft heart',
	              'Weight': 1
              },
              {
	              'Question': 'I am not really interested in others',
	              'Weight': -1
              },
              {
	              'Question': 'I take time out for others',
	              'Weight': 1
              },
              {
	              'Question': 'I feel others\' emotions',
	              'Weight': 1
              },
              {
	              'Question': 'I make people feel at ease',
	              'Weight': 1
              },

)
category_4 = ({
	              'Question': 'I am always prepared',
	              'Weight': 1
              },
              {
	              'Question': 'I leave my belongings around',
	              'Weight': -1
              },
              {
	              'Question': 'I pay attention to detail',
	              'Weight': 1
              },
              {
	              'Question': 'I make a mess of things',
	              'Weight': -1
              },
              {
	              'Question': 'I get chores done right away',
	              'Weight': 1
              },
              {
	              'Question': 'I like order',
	              'Weight': 1
              },
              {
	              'Question': 'I try to avoid my duties',
	              'Weight': -1
              },
              {
	              'Question': 'I follow a schedule',
	              'Weight': 1
              },
              {
	              'Question': 'I am thorough in my work',
	              'Weight': 1
              },
              {
	              'Question': 'I often forget to put things back in their proper place',
	              'Weight': -1
              },
)
category_5 = ({
	              'Question': 'I have a rich vocabulary',
	              'Weight': 1
              },
              {
	              'Question': 'I have difficulty understanding abstract ideas',
	              'Weight': -1
              },
              {
	              'Question': 'I have a vivid imagination',
	              'Weight': 1
              },
              {
	              'Question': 'I am not interested in abstract ideas',
	              'Weight': -1
              },
              {
	              'Question': 'I have excellent ideas',
	              'Weight': 1
              },
              {
	              'Question': 'I do not have a good imagination',
	              'Weight': -1
              },
              {
	              'Question': 'I am quick to understand things',
	              'Weight': 1
              },
              {
	              'Question': 'I spend time reflecting on things',
	              'Weight': 1
              },
              {
	              'Question': 'I am full of ideas',
	              'Weight': 1
              },
              {
	              'Question': 'I often use difficult words',
	              'Weight': 1
              },

)

categories = ('Extraversion', 'Neurotism', 'Agreeableness', 'Conscientiousness', 'Openness')

personality = (
	(
		{"title": "YOU ARE AN INTROVERT",
		 "description": "Extraversion refers to the energy you draw from social interactions. \
You have a hard time making small talk or introducing yourself, feel worn out after socializing, avoid large groups, \
are more reserved. A low extraversion score can mean you prefer to spend time alone or with a small group \
of close friends. You might also be a more private person when it comes to sharing details about your life. \
This might come across as standoffish to others. Introverted people are known for thinking things through \
before they speak, enjoying small, close groups of friends and one-on-one time, needing time alone to recharge, \
and being upset by unexpected changes or last-minute surprises. Introverts are not necessarily shy and may not \
even avoid social situations, but they will definitely need some time alone or just with close friends or family \
after spending time in a big crowd."
		 },
		{"title": "YOU ARE AN AMBIVERT",
		 "description": "Extraversion refers to the energy you draw from social interactions. \
Since introverts and extroverts are the extremes of the scale, the rest of us fall somewhere in the middle. Many of us\
lean one way or the other, but there are some who are quite balanced between the two tendencies. \
Ambiverts exhibit both extroverted and introverted tendencies. This means that they generally enjoy being around people,\
but after a long time this will start to drain them. Similarly, they enjoy solitude and quiet, but not for too long. \
Ambiverts recharge their energy levels with a mixture of social interaction and alone time."
		 },

		{"title": "YOU ARE AN EXTROVERT",
		 "description": "Extraversion refers to the energy you draw from social interactions. \
You seek excitement or adventure, make friends easily, speak without thinking, enjoy being active with others. \
If you score high on extraversion, you might consider yourself an extrovert. You might enjoy attention and \
feel recharged after spending time with friends. You likely feel your best when in a large group of people. \
On the other hand, you may have trouble spending long periods of time alone. \
"
		 }
	),
	(
		{"title": "LOW NEUROTISM",
		 "description": '''
         Neurotism describes a tendency to have unsettling thoughts and feelings. 
You are likely to keep calm in stressful situations, are more optimistic, worry less, have a more stable mood. 
A low neurotism score can mean you’re confident. You may have more resilience and find it easy to keep calm under stress. Relaxation might also come more easily to you. Try to keep in mind that this might not be as easy for those around you, so be patient. 

         '''},
		{"title": "HIGH NEUROTISM",
		 "description": '''
         Neurotism describes a tendency to have unsettling thoughts and feelings.

You have a high tendency to feel vulnerable or insecure, get stressed easily, struggle with difficult situations, have mood swings.
If you score high on neurotism, you may blame yourself when things go wrong. You might also get frustrated with yourself easily, especially if you make a mistake. Chances are, you’re also prone to worrying. 

But you’re likely also more introspective than others, which helps you to examine and understand your feelings.

         '''},
	),
	(
		{"title": "LOW AGREEABLENESS", "description": "Agreeableness refers to a desire to keep things running smoothly. \
You are likely to be stubborn, find it difficult to forgive mistakes, are self-centered, have less compassion for others. \
A low agreeableness score may mean you tend hold grudges. You might also be less sympathetic with others. \
But you are also likely avoid the pitfalls of comparing yourself to others or caring about what others think of you. "},
		{"title": "HIGH AGREEABLENESS", "description": "Agreeableness refers to a desire to keep things running smoothly. \
You are always ready to help out, are caring and honest, are interested in the people around you, believe the best about others. \
If you score high in agreeableness, you you’re helpful and cooperative. Your loved ones may often turn to you for help. \
People might see you as trustworthy. You may be the person others seek when they’re trying to resolve a disagreement. \
In some situations, you might a little too trusting or willing to compromise. \
Try to balance your knack for pleasing others with self-advocacy. "
		 },
	),
	(
		{"title": "LOW CONSCIENTIOUSNESS", "description": "Conscientiousness describes a careful, detail-oriented nature. \
A low score on conscientiousness might mean you are less organized, complete tasks in a less structured way, \
take things as they come, finish things at the last minute are impulsive. \
A low conscientiousness score might mean you prefer a setting without structure. \
You may prefer doing things at your own pace to working on a deadline. This might make you appear unreliable to others. "
		 },
		{"title": "HIGH CONSCIENTIOUSNESS", "description": "Conscientiousness describes a careful, detail-oriented nature. \
You likely keep things in order, come prepared to school or work, are goal-driven, are persistent. \
If you are a conscientious person, you might follow a regular schedule and have a knack for keeping track of details. \
You likely deliberate over options and work hard to achieve your goals. Coworkers and friends might see you as a reliable,\
fair person. You may tend to micromanage situations or tasks. You might also be cautious or difficult to please. "},
	),
	(
		{"title": "LOW OPENNESS", "description": "Openness, or openness to experience, refers to a sense of curiosity \
about others and the world. A low openness score might mean you prefer to do things in a familiar way, avoid change,\
are more traditional in your thinking. A low openness score can mean you consider concepts in straightforward ways. \
Others likely see you as being grounded and down-to-earth. "},
		{"title": "HIGH OPENNESS", "description": "Openness, or openness to experience, refers to a sense of curiosity\
about others and the world. If you scored high on openness, you might enjoy trying new things, be more creative, \
have a good imagination, be willing to consider new ideas. A high score on openness can mean you have broad interests. \
You may enjoy solving problems with new methods and find it easy to think about things in different ways. \
Being open to new ideas may help you adjust easily to change. Just make sure to keep an eye out for \
any situations where you might need to establish boundaries, whether that be with family members or \
your work-life balance."
		 },
	)

)

our_categories = (category_1, category_2, category_3, category_4, category_5)


def get_score(score):
	"""
    This function returns a point based on the score range (-1,0,1).
    :param score: the score.
    :return: the point.
    """
	if score < -1:
		return 1
	if score > 1:
		return 3
	return 2


def get_personality(score, category):
	"""
    This function gets the category and returns the personality description based on the score
    :param score:  The score
    :param category: The personality category
    :return: a string of the description
    """
	if category != 'Extraversion':
		if score > 0:
			return json.dumps(personality[categories.index(category)][1])
		else:
			return json.dumps(personality[categories.index(category)][0])
	else:
		if score < -1:
			my_personality = json.dumps(personality[categories.index(category)][0])
			return my_personality
		if score > 1:
			my_personality = json.dumps(personality[categories.index(category)][2])
			return my_personality
		my_personality = json.dumps(personality[categories.index(category)][1])
		return my_personality


def display(request):
	"""
    This function returns the message for an alert.
    :param request: HTTP request
    :return: This returns a list containing the message, the status and the icon.
    """
	if 'message' in request.session:
		message = request.session['message']
		status = request.session['status']
		icon = request.session['icon']
		del request.session['message'], request.session['status'], request.session['icon']
		return message, status, icon
	return None


def send_verification(request, user):
	"""
    This function sends a verification email to the target user
    :param request: HTTP request
    :param user: The user instance
    :return:
    """
	request.session['code'] = request.POST['csrfmiddlewaretoken']
	link = f'https://{request.get_host()}/account/verify/?code={request.POST["csrfmiddlewaretoken"]}&' \
	       f'email={request.POST["email"]}'
	request.session['verification_sent'] = True
	send_email(user.first_name, 'Email Verification', 'We are excited to have you on Datefix', [request.POST['email']],
	           link, None)


def dict_to_zip(data):
	"""
    This function takes a set of dictionary and partitions the items into lists and pack them into one list.
    :param data:  a dictionary object.
    :return: a zip iterable.
    """
	questions = set([x['Question'] for x in data])
	weights = (x['Weight'] for x in data)
	count = set([data.index(x) for x in data])
	return zip(count, questions, weights)


def had_session(user):
	"""
    This function checks if a user still has an existing chat session
    :param user: User instance
    :return: a boolean result.
    """
	return user.jilted_matches or user.couple_ids


from services.email_service import send_email
