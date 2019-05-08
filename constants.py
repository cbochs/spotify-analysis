# DEFINE A FEW STANDARD DATETIME STYLES
DATETIME_FORMAT_MS = '%Y-%m-%dT%H:%M:%S.%fZ'
DATETIME_FORMAT_LONG = '%Y-%m-%dT%H:%M:%SZ'
DATETIME_FORMAT_SHORT = '%Y-%m-%d'
DATETIME_FORMAT_YR_MTH = '%Y-%m'
DATETIME_FORMAT_YEAR = '%Y'

DATETIME_FORMAT_DEFAULT = '%Y-%m-%dT%H:%M:%SZ'
DATETIME_FORMAT_FILENAME = '%Y-%m-%dT%H-%M-%SZ'

# DEFINE REQUIRED SCOPES FOR BACKUP/ARCHIVING
SCOPE = ','.join(['playlist-read-private',
                  'playlist-read-collaborative',
                  'playlist-modify-public',
                  'playlist-modify-private',
                  'user-library-read',
                  'user-read-recently-played'])