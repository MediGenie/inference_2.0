FROM node:16 as frontend

WORKDIR /app
COPY ./mnist /app
RUN yarn install && yarn build


FROM python:3.10

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy poetry files
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy source code
COPY . .

#Copy frontend
COPY --from=frontend /app/build /app/mnist/build
