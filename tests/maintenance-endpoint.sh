#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
helper_template="${MAINTENANCE_ENDPOINT_HELPER:-$repo_root/roles/server/templates/maintenance-endpoint.sh.j2}"
test_dir="$(mktemp -d)"
fake_bin="$test_dir/bin"
docker_log="$test_dir/docker.log"
helper_pid=""
fifo_fd_open=0

cleanup() {
  local original_status=$?
  trap - EXIT
  set +e
  if [ "$fifo_fd_open" -eq 1 ]; then
    exec 3>&-
    fifo_fd_open=0
  fi
  if [ -n "$helper_pid" ]; then
    if kill -0 "$helper_pid" 2>/dev/null; then
      kill -TERM "$helper_pid" 2>/dev/null
    fi
    wait "$helper_pid" 2>/dev/null || true
    helper_pid=""
  fi
  rm -rf "$test_dir"
  exit "$original_status"
}
trap cleanup EXIT

fail() {
  printf 'maintenance endpoint trap check failed: %s\n' "$*" >&2
  exit 1
}

assert_eq() {
  [ "$1" = "$2" ] || fail "expected [$2], got [$1]"
}

assert_file_exists() {
  [ -e "$1" ] || fail "expected file to exist: $1"
}

command_line() {
  local line
  local last_line=""
  while IFS= read -r line; do
    last_line="$line"
  done < "$docker_log"
  printf '%s' "$last_line"
}

ordinary_restore_count() {
  local compose_arg
  local count=0
  local line
  printf -v compose_arg '%q' "$job_dir/compose.yaml"
  while IFS= read -r line; do
    case "$line" in
      *" up -d")
        case " $line " in
          *" $compose_arg "*|*"=$compose_arg "*) ((count += 1)) ;;
        esac
        ;;
    esac
  done < "$docker_log"
  printf '%s' "$count"
}

wait_for_command() {
  local expected="$1"
  local line
  local attempt
  for ((attempt = 0; attempt < 100; attempt += 1)); do
    while IFS= read -r line; do
      [ "$line" = "$expected" ] && return 0
    done < "$docker_log"
    read -r -t 0.1 -u 3 _ || true
  done
  fail "timed out waiting for [$expected]"
}

compose_command() {
  local compose_file="$1"
  local command="$2"
  shift 2
  local rendered
  printf -v rendered '%q ' compose --project-directory "$job_dir" -f "$compose_file" "$command" "$@"
  printf '%s' "${rendered% }"
}

render_helper() {
  job_dir="$test_dir/$1"
  mkdir -p "$job_dir"
  local rendered_helper
  rendered_helper="$(<"$helper_template")"
  rendered_helper="${rendered_helper//\{\{ friend.name \}\}/test-friend}"
  printf '%s\n' "$rendered_helper" > "$job_dir/maintenance-endpoint.sh"
  : > "$job_dir/compose.yaml"
  : > "$job_dir/compose.maintenance.yaml"
  chmod +x "$job_dir/maintenance-endpoint.sh"
}

mkdir -p "$fake_bin"
cat > "$fake_bin/docker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

printf -v command_line '%q ' "$@"
printf '%s\n' "${command_line% }" >> "$FAKE_DOCKER_LOG"

if [ "${FAKE_DOCKER_FAIL_NORMAL_UP:-}" = 1 ] &&
  [ "$#" -ge 3 ] &&
  [[ "${@: -3:1}" == */compose.yaml ]] &&
  [ "${@: -2:1}" = up ] &&
  [ "${@: -1}" = -d ]; then
  exit 42
fi

if [ "${FAKE_DOCKER_FAIL_MAINTENANCE_DOWN:-}" = 1 ] &&
  [ "$#" -ge 3 ] &&
  [[ "${@: -3:1}" == */compose.maintenance.yaml ]] &&
  [ "${@: -2:1}" = down ] &&
  [ "${@: -1}" = --remove-orphans ]; then
  exit 55
fi
EOF
chmod +x "$fake_bin/docker"

cat > "$fake_bin/rm" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

if [ "${FAKE_RM_FAIL:-}" = 1 ]; then
  exit 66
fi

exec /bin/rm "$@"
EOF
chmod +x "$fake_bin/rm"

render_helper normal
: > "$docker_log"
set +e
printf '\n' | PATH="$fake_bin:$PATH" FAKE_DOCKER_LOG="$docker_log" \
  "$job_dir/maintenance-endpoint.sh" >/dev/null
normal_status=$?
set -e
assert_eq "$normal_status" 0
normal_restore="$(compose_command "$job_dir/compose.yaml" up -d)"
assert_eq "$(command_line)" "$normal_restore"

render_helper term
: > "$docker_log"
fifo="$test_dir/maintenance-input"
mkfifo "$fifo"
exec 3<> "$fifo"
fifo_fd_open=1
maintenance_up="$(compose_command "$job_dir/compose.maintenance.yaml" up -d)"
term_restore="$(compose_command "$job_dir/compose.yaml" up -d)"
PATH="$fake_bin:$PATH" FAKE_DOCKER_LOG="$docker_log" \
  "$job_dir/maintenance-endpoint.sh" < "$fifo" >/dev/null &
helper_pid=$!
wait_for_command "$maintenance_up"
kill -TERM "$helper_pid"
set +e
wait "$helper_pid"
term_status=$?
set -e
helper_pid=""
exec 3>&-
fifo_fd_open=0
assert_eq "$term_status" 143
assert_eq "$(command_line)" "$term_restore"
assert_eq "$(ordinary_restore_count)" 1

render_helper restore-failure
: > "$docker_log"
set +e
printf '\n' | PATH="$fake_bin:$PATH" FAKE_DOCKER_LOG="$docker_log" \
  FAKE_DOCKER_FAIL_NORMAL_UP=1 "$job_dir/maintenance-endpoint.sh" >/dev/null
restore_failure_status=$?
set -e
assert_eq "$restore_failure_status" 42
assert_file_exists "$job_dir/compose.maintenance.yaml"
assert_file_exists "$job_dir/maintenance-endpoint.sh"

render_helper maintenance-down-failure
: > "$docker_log"
set +e
printf '\n' | PATH="$fake_bin:$PATH" FAKE_DOCKER_LOG="$docker_log" \
  FAKE_DOCKER_FAIL_MAINTENANCE_DOWN=1 "$job_dir/maintenance-endpoint.sh" >/dev/null
maintenance_down_status=$?
set -e
assert_eq "$maintenance_down_status" 55
maintenance_down_restore="$(compose_command "$job_dir/compose.yaml" up -d)"
assert_eq "$(command_line)" "$maintenance_down_restore"
assert_eq "$(ordinary_restore_count)" 1
assert_file_exists "$job_dir/compose.maintenance.yaml"
assert_file_exists "$job_dir/maintenance-endpoint.sh"

render_helper artifact-removal-failure
: > "$docker_log"
set +e
printf '\n' | PATH="$fake_bin:$PATH" FAKE_DOCKER_LOG="$docker_log" \
  FAKE_RM_FAIL=1 "$job_dir/maintenance-endpoint.sh" >/dev/null
artifact_removal_status=$?
set -e
assert_eq "$artifact_removal_status" 66
artifact_removal_restore="$(compose_command "$job_dir/compose.yaml" up -d)"
assert_eq "$(command_line)" "$artifact_removal_restore"
assert_eq "$(ordinary_restore_count)" 1
assert_file_exists "$job_dir/compose.maintenance.yaml"
assert_file_exists "$job_dir/maintenance-endpoint.sh"

printf 'maintenance endpoint trap checks passed\n'
