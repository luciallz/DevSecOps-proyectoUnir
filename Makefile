.PHONY: up down restart logs clean sonar-status

up:
	docker-compose up -d --build

down:
	docker-compose down

restart:
	docker-compose down && docker-compose up -d --build

logs:
	docker-compose logs -f

clean:
	docker system prune -f
	sudo rm -rf ./sonarqube_data ./sonarqube_logs ./sonarqube_extensions ./sonarqube_temp
	sudo rm -rf ./jenkins_home

sonar-status:
	curl -s http://localhost:9000/api/system/health | jq
	
