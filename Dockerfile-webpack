FROM node:8

ENV PATH="/webpack/node_modules/.bin:${PATH}"

RUN mkdir /webpack
WORKDIR /webpack

ADD package.json /webpack/
RUN npm install

CMD webpack --watch
