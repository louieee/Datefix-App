def purify_email(email: str):
	email = email.lower()
	email = email.replace(' ', '')
	return email

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


def get_username():
	"""
    This function generates a random username for a particular user.
    :return: a string => the username
    """
	username = f'Datefix-User-{str(random.randint(1, 123456789))}'
	if User.objects.filter(username__iexact=username).exists():
		return get_username()
	return username

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


def get_path(request):
	"""
    This function gets the current url
    :param request: HTTP request
    :return: it returns a string
    """
	return f'http://{str(request.get_host())}{str(request.get_full_path(True))}'
