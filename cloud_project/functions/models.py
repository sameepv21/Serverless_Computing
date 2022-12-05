from django.db import models

class File(models.Model):
    file = models.FileField(upload_to='files/')
    function_name = models.CharField(max_length=255)

    def __str__(self):
        return self.function_name
