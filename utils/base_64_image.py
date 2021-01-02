from drf_extra_fields import fields
# .fields import Base64ImageField


class Base64ImageField(fields.Base64ImageField):
    ALLOWED_TYPES = (
        "jpeg",
        "jpg",
        "png",
        "gif",
        "svg",
    )
