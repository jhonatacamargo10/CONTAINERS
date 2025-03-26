import os
import subprocess
import platform

def verificar_instalar_docker():
    """Verifica se o Docker está instalado e instala se necessário."""
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("[✔] Docker já está instalado.")
    except subprocess.CalledProcessError:
        print("[✘] Docker não encontrado! Instalando...")
        so = platform.system()

        if so == "Linux":
            distro = subprocess.run(["lsb_release", "-is"], capture_output=True, text=True).stdout.strip().lower()
            
            if "ubuntu" in distro or "debian" in distro:
                os.system("apt-get update && apt-get install -y docker.io")
            elif "centos" in distro or "oracle" in distro:
                os.system("yum install -y docker && systemctl start docker && systemctl enable docker")
            else:
                print("Distribuição não suportada. Instale o Docker manualmente.")
                exit(1)

        elif so == "Darwin":
            print("Instale o Docker manualmente no macOS via https://docs.docker.com/desktop/install/mac/")
            exit(1)

        else:
            print("Sistema operacional não suportado.")
            exit(1)
        
        print("[✔] Docker instalado com sucesso!")

def iniciar_swarm():
    """Inicializa o Docker Swarm se ainda não estiver ativo, e verifica se o nó é um manager."""
    try:
        result = subprocess.run(["docker", "info"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if "Swarm: active" in result.stdout:
            if "NodeID" not in result.stdout:  # Verifica se o nó é um manager
                print("[✘] Este nó não é um manager do Docker Swarm. Promovendo o nó para manager...")
                os.system("docker swarm init")
            else:
                print("[✔] Docker Swarm já está ativo e o nó é um manager.")
        else:
            print("[✘] Docker Swarm não detectado. Inicializando...")
            os.system("docker swarm init")
            print("[✔] Docker Swarm inicializado e nó promovido a manager.")
    except subprocess.CalledProcessError as e:
        print(f"[✘] Erro ao verificar ou inicializar o Docker Swarm: {e}")
        exit(1)

def criar_arquivos():
    """Cria os arquivos Docker necessários."""
    # Criando Dockerfile do PHP-FPM
    with open("Dockerfile-php", "w") as f:
        f.write("""\
FROM php:7.4-fpm
RUN docker-php-ext-install mysqli pdo pdo_mysql
COPY index.php /var/www/html/index.php
""")

    # Criando arquivo index.php para teste
    with open("index.php", "w") as f:
        f.write("""\
<?php
phpinfo();
?>
""")

    # Criando docker-compose.yml para serviços no Swarm
    with open("docker-compose.yml", "w") as f:
        f.write("""\
version: '3.8'

services:
  mysql:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: appdb
      MYSQL_USER: user
      MYSQL_PASSWORD: password
    networks:
      - minha_rede

  php-fpm:
    image: php-fpm:latest  # Substitua com a imagem criada manualmente
    deploy:
      replicas: 3
    networks:
      - minha_rede

  nginx:
    image: nginx:latest
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - php-fpm
    networks:
      - minha_rede

networks:
  minha_rede:
    driver: overlay
""")

    # Criando arquivo de configuração do Nginx
    with open("nginx.conf", "w") as f:
        f.write("""\
events {}

http {
    upstream php_fpm_backend {
        server php-fpm:9000;
    }

    server {
        listen 80;

        location / {
            fastcgi_pass php_fpm_backend;
            fastcgi_index index.php;
            fastcgi_param SCRIPT_FILENAME /var/www/html/index.php;
            include fastcgi_params;
        }
    }
}
""")

def construir_imagem_php_fpm():
    """Constrói manualmente a imagem do PHP-FPM"""
    print("[✔] Construindo a imagem do PHP-FPM...")
    subprocess.run(["docker", "build", "-t", "php-fpm:latest", "-f", "Dockerfile-php", "."], check=True)

def subir_servicos():
    """Sobe os serviços usando Docker Swarm."""
    os.system("docker stack deploy -c docker-compose.yml minha_aplicacao")

def main():
    verificar_instalar_docker()
    iniciar_swarm()
    criar_arquivos()
    construir_imagem_php_fpm()  # Construir imagem PHP-FPM
    print("[✔] Arquivos Docker criados!")
    subir_servicos()
    print("[✔] Serviços iniciados!")

if __name__ == "__main__":
    main()
