// src/components/SettingsModal.js
import React from 'react';
import {
  Keyboard,
  KeyboardAvoidingView,
  Modal,
  Text,
  TextInput,
  TouchableOpacity,
  TouchableWithoutFeedback,
  Platform,
  View,
} from 'react-native';
import { styles } from '../styles/appStyles';

const MODEL_OPTIONS = [
  { key: 'n', label: 'YOLOv8n', interval: 50 },
  { key: 'm', label: 'YOLOv8m', interval: 200 },
  { key: 'x', label: 'YOLOv8x', interval: 500 },
];

export function SettingsModal({
  visible,
  model,
  onSelectModel,
  apiHost,
  onChangeApiHost,
  onClearIds,
  onRestartApp,
  showLabels,
  onToggleLabels,
  onClose,
}) {
  return (
    <Modal visible={visible} animationType="fade" transparent>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <TouchableWithoutFeedback onPress={Keyboard.dismiss} accessible={false}>
          <View style={styles.settingsBackdrop}>
            <View style={styles.settingsCard}>
              <Text style={styles.settingsTitle}>Settings</Text>

              <Text style={styles.settingsLabel}>Model</Text>
              <View>
                {MODEL_OPTIONS.map((opt) => (
                  <TouchableOpacity
                    key={opt.key}
                    style={[
                      styles.modelOption,
                      model === opt.key && styles.modelOptionActive,
                    ]}
                    onPress={() => onSelectModel(opt.key)}
                  >
                    <Text style={styles.modelOptionText}>{opt.label}</Text>
                    <Text style={styles.modelOptionSub}>
                      {opt.interval}ms interval
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.settingsLabel}>Backend IP (no http/port)</Text>
              <TextInput
                style={styles.input}
                value={apiHost}
                onChangeText={onChangeApiHost}
                autoCapitalize="none"
                autoCorrect={false}
                placeholder="192.168.0.100"
                placeholderTextColor="#8aa0b3"
                returnKeyType="done"
                blurOnSubmit
                onSubmitEditing={Keyboard.dismiss}
              />

              <TouchableOpacity style={styles.actionButton} onPress={onClearIds}>
                <Text style={styles.detectText}>Clear Backend IDs</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.actionButton} onPress={onRestartApp}>
                <Text style={styles.detectText}>Restart App</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.actionButton} onPress={onToggleLabels}>
                <Text style={styles.detectText}>
                  {showLabels ? 'Hide Box Text' : 'Show Box Text'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.closeButton} onPress={onClose}>
                <Text style={styles.detectText}>Close</Text>
              </TouchableOpacity>
            </View>
          </View>
        </TouchableWithoutFeedback>
      </KeyboardAvoidingView>
    </Modal>
  );
}
