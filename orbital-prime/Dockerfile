FROM apify/actor-node:20

WORKDIR /usr/src/app

COPY package.json ./
RUN npm install apify@3.4.2 --omit=dev --omit=optional \
    && echo "npm install OK"

COPY js ./js
COPY vendor ./vendor
COPY .actor ./.actor

CMD ["node", "js/actor-main.js"]
