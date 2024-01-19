cat << EOF > .env
UID=$(id -u)
USER=$(id -u -n)
GID=$(id -g)
GROUP=$(id -g -n)
EOF

