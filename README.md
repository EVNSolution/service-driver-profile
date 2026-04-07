# service-driver-profile

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

아키텍처 정본:
- `../../docs/boundaries/`
- `../../docs/mappings/`
