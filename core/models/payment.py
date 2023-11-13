from django.db import models


# Create your models here.

class Payment(models.Model):
    payer = models.ForeignKey("core.User", on_delete=models.CASCADE)
    package = models.CharField(max_length=10, choices=(('REGULAR', 'REGULAR'), ('PREMIUM', 'PREMIUM')), default='BASIC')
    date_of_payment = models.DateTimeField(auto_now=True)
    duration = models.CharField(max_length=10, choices=(('QUARTERLY', 'QUARTERLY'), ('YEARLY', 'YEARLY')), null=True, blank=True)
    status = models.CharField(max_length=10, choices=(('PENDING', 'PENDING'), ('PAID', 'PAID'), ('FAILED', 'FAILED')),
                              default='PENDING')
    expiry_date = models.DateTimeField(null=True, default=None)
    tx_ref = models.CharField(max_length=32, null=True, blank=True)
