from django.db import models

class Test(models.Model):
    id = models.AutoField(primary_key=True)
    test_name = models.CharField(max_length=100)
    normal_range = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Tests'

class TestParameter(models.Model):
    id = models.AutoField(primary_key=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, db_column='test_id', related_name='parameters')
    parameter_name = models.CharField(max_length=100)
    unit = models.CharField(max_length=50, default='', blank=True)
    normal_range = models.CharField(max_length=100, default='', blank=True)
    display_order = models.IntegerField(default=0)
    formula = models.TextField(null=True, blank=True)
    parameter_type = models.CharField(max_length=50, default='text')

    class Meta:
        db_table = 'Test_Parameters'

class TestPackage(models.Model):
    id = models.AutoField(primary_key=True)
    package_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tests = models.ManyToManyField(Test, db_table='Test_Package_Tests', related_name='packages')

    class Meta:
        db_table = 'Test_Packages'
