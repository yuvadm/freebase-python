
from session import HTTPMetawebSession, MetawebError, attrdict

from mqlkey import quotekey, unquotekey

LITERAL_TYPE_IDS = set([
  "/type/int",
  "/type/float",
  "/type/boolean",
  "/type/rawstring",
  "/type/uri",
  "/type/text",
  "/type/datetime",
  "/type/bytestring",
  "/type/id",
  "/type/key",
  "/type/value",
  "/type/enumeration"
])
