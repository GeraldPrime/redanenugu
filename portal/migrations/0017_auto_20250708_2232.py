from django.db import migrations

def migrate_category_data(apps, schema_editor):
    """Migrate data from CharField to ForeignKey"""
    Member = apps.get_model('portal', 'Member')
    Category = apps.get_model('portal', 'Category')
    
    for member in Member.objects.all():
        if member.company_category:
            try:
                category = Category.objects.get(code=member.company_category)
                member.company_category_new = category
                member.save()
                print(f"Migrated member {member.id}: {member.company_category} -> {category.name}")
            except Category.DoesNotExist:
                print(f"Warning: Category '{member.company_category}' not found for member {member.id}")

def reverse_migrate_category_data(apps, schema_editor):
    """Reverse operation - copy data back"""
    Member = apps.get_model('portal', 'Member')
    
    for member in Member.objects.all():
        if member.company_category_new:
            member.company_category = member.company_category_new.code
            member.save()

class Migration(migrations.Migration):
    dependencies = [
        ('portal', '0016_category'),
    ]

    operations = [
        migrations.RunPython(migrate_category_data, reverse_migrate_category_data),
    ]