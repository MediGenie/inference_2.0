import './App.scss';

import React, { Component, useEffect, useState } from 'react';

const MODEL_NAME = 'mnist';
const API_BASE_URL = '/';


function Model(props) {
  let { model } = props;
  return (
    <p>
      <h2>Model</h2>
      <pre>Name: {model.name}</pre>
      <pre>Created at: {model.created_at}</pre>
      <pre>Updated at: {model.updated_at}</pre>
      <pre>ID: {model.id}</pre>
    </p>
  );
};

function Job(props) {
  let { job } = props;
  if (!job) {
    return null;
  }

  return (
    <p>
      <h2>Job</h2>
      <pre>ID: {job.id}</pre>
      <pre>Created at: {job.created_at}</pre>
      <pre>Updated at: {job.updated_at}</pre>
      <pre>Status: {job.status}</pre>
      <pre>Progress: {job.progress}</pre>
      <pre>Result path: {job.result_path}</pre>
    </p>
  );
};

function Result(props) {
  let { job } = props;

  const [result, setResult] = useState();

  useEffect(() => {
    if (!job || !job.result_path) {
      return;
    }

    fetch(`${API_BASE_URL}results/${job.result_path}`)
      .then(res => res.text())
      .then(text => {
        setResult(text);
      });
  })

  if (!job || !job.result_path) {
    return null;
  }

  return (
    <p>
      <h2>Result</h2>
      <pre>Path: {job.result_path}</pre>
      <pre>Result: {result}</pre>
    </p>
  );
}

class App extends Component {
  state = {
    model: null,
    argument_infos: [],
    result_path: null,
    values: [],
    inputText: '',
    job: null,
    checker: null,
  }

  componentDidMount() {
    fetch(`${API_BASE_URL}models/`)
      .then(res => res.json())
      .then(data => {
        let model = data.find(model => model.name === MODEL_NAME);
        this.setState({ model: model });
      })
  }

  onChangeFileHandler(e) {
    let file = e.target.files[0];
    if (file) {
      console.log(file);
      this.setState({values: [...this.state.values, file]})
      } else {
      console.log("No file selected.")
      }
    }

  updateInputText(e) {
    this.setState({inputText: e.target.value})
    }
  
  onChangeTextHandler() {
    if (this.state.inputText !== '') {
      this.setState({
        values: [...this.state.values, this.state.inputText],
        inputText: '',
      })
      } else {
      console.log("Text empty.")
      }
    }

  onUploadHandler(_e) {
    let formData = new FormData();
    this.state.values.forEach((value) => formData.append("value_list", value));
    fetch(`${API_BASE_URL}uploads/`, {
      method: 'POST',
      body: formData,
    })
      .then(res => res.json())
      .then(file => {
        this.setState({argument_infos: [...file.argument_infos]});
      })
    ;
  }

  onSubmitHandler(_e) {
    let { model, argument_infos } = this.state;
    if (!argument_infos || !model) {
      return;
    }

    // Create job
    let data = {
      model_id: model.id,
      argument_infos,
    };

    fetch(`${API_BASE_URL}jobs/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
      .then(res => res.json())
      .then((job) => {
        // Create cheker interval
        let checker = setInterval(this.refreshJob.bind(this), 1000);
        this.setState({
          checker: checker,
          job: job,
        });
      });
  }

  refreshJob() {
    let { job, checker } = this.state;
    if (!job || job.status === 'failed' || job.status === 'completed') {
      clearInterval(checker);
      this.setState({
        checker: null,
      });
      return;
    }

    fetch(`${API_BASE_URL}jobs/${job.id}`)
      .then(res => res.json())
      .then(data => {
        this.setState({
          job: data,
        });
      });
  }

  render() {
    let { model } = this.state;
    if (!model) {
      return <div>Loading...</div>
    }

    return (
      <>
        <Model model={model} />

        <div id="input">
          <h2>Input Values</h2>
          <input type="file" onChange={this.onChangeFileHandler.bind(this)} style={{ display: '' }}/>
          <input type="text" value={this.state.inputText} onChange={this.updateInputText.bind(this)} />
          <button onClick={this.onChangeTextHandler.bind(this)}>Text Push</button>
          {this.state.values && this.state.values.map((value, index) => (
            <div key={index}>
              <p>Index:{index}</p>
              <p>Type: {value instanceof File ? "file" : "text"} </p>
              <p>Value: {value instanceof File ? value.name : value}</p>
            </div>
          ))}
          <div>
            <button onClick={this.onUploadHandler.bind(this)}>Upload </button>
          </div>
        </div>

        {this.state.argument_infos.map((item, index) => (
          <p key={index}>Path: {item.value}, Type: {item.type}, Index: {item.index} </p>
        ))}
        <p>
          <h2>Run</h2>
          <button onClick={this.onSubmitHandler.bind(this)}>Run</button>
        </p>

        <Job job={this.state.job} />

        <Result job={this.state.job} />
      </>
    );
  }
}


export default App;
