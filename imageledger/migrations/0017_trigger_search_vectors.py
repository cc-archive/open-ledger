from django.db import migrations

class Migration(migrations.Migration):

    """
    Create a trigger for automatic updates of search vector columns. Every time an item is updated or inserted,
    the search vector columns are recomputed. We also create an index for search vector column here, which is 
    critical for decent performance.

    See imageledger.models.Image.search_vectors
    """
    dependencies = [
        ('imageledger', '0016_image_search_vectors'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX searchvec_idx ON image USING gin(search_vectors);"
            "CREATE FUNCTION build_search_vectors() RETURNS trigger AS $$ "
            "begin"
            "  new.search_vectors :="
            "    setweight(to_tsvector(coalesce(new.title)), 'A') || "
            "    setweight(array_to_tsvector(coalesce(new.tags_list, ARRAY[]::TEXT[])), 'B') || "
            "    setweight(to_tsvector(coalesce(new.creator)), 'C'); "
            "  return new;"
            "end"
            "$$ LANGUAGE plpgsql;"
            "CREATE TRIGGER searchvecupdate BEFORE INSERT OR UPDATE "
            "ON image FOR EACH ROW EXECUTE PROCEDURE build_search_vectors(); "
        )
    ]
