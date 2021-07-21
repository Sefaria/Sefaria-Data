import django
django.setup()
import yutil


# yutil.load_venice_data()
va = yutil.VersionAlignment(yutil.venice, yutil.gugg, "./v_comp", skip_mishnah=True)

# va.generate_comparisons()
# print(va.errors)