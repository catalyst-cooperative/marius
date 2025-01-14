//
// Created by Jason Mohoney on 9/30/21.
//

#include "common/pybind_headers.h"

#include "nn/layers/gnn/rgcn_layer.h"

void init_rgcn_layer(py::module &m) {

    py::class_<RGCNLayer, GNNLayer, shared_ptr<RGCNLayer>>(m, "RGCNLayer")
            .def_readwrite("options", &RGCNLayer::options_)
            .def_readwrite("num_relations", &RGCNLayer::num_relations_)
            .def_readwrite("relation_matrices_", &RGCNLayer::relation_matrices_)
            .def_readwrite("inverse_relation_matrices_", &RGCNLayer::inverse_relation_matrices_)
            .def_readwrite("self_matrix_", &RGCNLayer::self_matrix_)
            .def(py::init<shared_ptr<LayerConfig>, int, torch::Device>(),
                 py::arg("layer_config"),
                 py::arg("num_relations"),
                 py::arg("device"))
            .def(py::init([](int input_dim,
                             int output_dim,
                             int num_relations,
                             std::optional<torch::Device> device,
                             InitConfig init,
                             bool bias,
                             InitConfig bias_init,
                             string activation) {

                     auto layer_config = std::make_shared<LayerConfig>();
                     layer_config->input_dim = input_dim;
                     layer_config->output_dim = output_dim;
                     layer_config->type = LayerType::GNN;

                     auto layer_options = std::make_shared<GNNLayerOptions>();
                     layer_config->options = layer_options;

                     layer_config->init = std::make_shared<InitConfig>(init);
                     layer_config->bias = bias;
                     layer_config->bias_init = std::make_shared<InitConfig>(bias_init);
                     layer_config->optimizer = nullptr;
                     layer_config->activation = getActivationFunction(activation);

                     torch::Device torch_device = torch::kCPU;
                     if (device.has_value()) {
                         torch_device = device.value();
                     }

                     return std::make_shared<RGCNLayer>(layer_config, num_relations, torch_device);

                 }), py::arg("input_dim"),
                 py::arg("output_dim"),
                 py::arg("num_relations"),
                 py::arg("device") = py::none(),
                 py::arg("init") = InitConfig(InitDistribution::GLOROT_UNIFORM, nullptr),
                 py::arg("bias") = false,
                 py::arg("bias_init") = InitConfig(InitDistribution::ZEROS, nullptr),
                 py::arg("activation") = "none")
            .def("reset", &RGCNLayer::reset)
            .def("forward", &RGCNLayer::forward,
                 py::arg("inputs"),
                 py::arg("dense_graph"),
                 py::arg("train") = true);
}