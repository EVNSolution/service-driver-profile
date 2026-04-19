# service-driver-profile

## Purpose / Boundary

이 repo는 배송원 기본 `profile` 정본을 소유한다.

현재 역할:
- 배송원 기본정보 CRUD
- 계정 연결 참조
- 회사/플릿 참조와 EV ID 중복 검사
- 재직 상태와 자격 상태 정본 관리

포함:
- Django/DRF runtime
- driver profile migration
- driver profile test
- service-local seed command

포함하지 않음:
- account/auth 정본
- 조직 정본
- vehicle assignment 로직
- 플랫폼 전체 compose와 gateway 설정

## Runtime Contract / Local Role

- compose service는 `driver-profile-api` 다.
- gateway prefix는 `/api/drivers/` 다.
- driver profile truth만 소유하고, auth/org/assignment는 참조만 한다.

## Local Run / Verification

- local run: `python3 manage.py runserver 0.0.0.0:8000`
- local test: `python3 manage.py test -v 2`

## Image Build / Deploy Contract

- prod contract is build, test, and immutable image publish only
- production runtime rollout ownership belongs to `runtime-prod-release`
- build and publish auth uses `ECR_BUILD_AWS_ROLE_ARN` plus shared `AWS_REGION`


- GitHub Actions workflow 이름은 `Build service-driver-profile image`다.
- workflow는 immutable `service-driver-profile:<sha>` 이미지를 ECR로 publish 한다.
- runtime rollout은 `../runtime-prod-release/` 가 소유한다.
- production runtime shape와 canonical inventory는 `../runtime-prod-platform/` 이 소유한다.

## Environment Files And Safety Notes

- profile truth와 account/auth truth를 같은 repo에서 바꾸지 않는다.
- downstream UI는 driver profile을 넓게 읽지만, write truth는 이 service boundary 안에만 둔다.

## Key Tests Or Verification Commands

- full Django tests: `python3 manage.py test -v 2`
- external smoke는 `/api/drivers/` protected read path를 포함하는 편이 낫다.

## Root Docs / Runbooks

- `../../docs/boundaries/`
- `../../docs/mappings/`
- `../../docs/runbooks/ev-dashboard-ui-smoke-and-decommission.md`
