select *
from {{ ref('cleaned') }}
where RETURN_CODE = 200