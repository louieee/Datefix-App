from django.urls import path
from core.apis.account import matching, get_data, personality, get_couple
urlpatterns = [
	path('match/', matching, name='match'),
	path('get_data/<type_>/', get_data, name="get_data"),
	path('personality_test/submit/', personality, name='submit_test'),
	path('api/get_couple/<int:couple_id>/', get_couple, name="get_couple")

]
