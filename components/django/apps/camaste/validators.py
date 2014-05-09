from django.core.validators import RegexValidator

is_username = RegexValidator(r'^[a-zA-Z0-9]{3,30}$',
                             message='Must only contain letters and numbers',
                             code='invalid_username')

is_modelname = RegexValidator(r'^[a-zA-Z0-9][a-zA-Z0-9 ]{2,29}$',
							  message='Must not contain special characters',
							  code='invalid_modelname')